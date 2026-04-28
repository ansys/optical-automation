# Python Script, API Version = V252
from __future__ import print_function

"""
Script overview
---------------
This script prepares a Speos Interactive Simulation by:
1) Collecting all Speos materials in the document.
2) Resolving every linked geometry (faces/features) to its owning DesignBody
   (document-level IDocObject), so the simulation runs on full bodies.
3) Optionally filtering by visibility.
4) Deduplicating bodies (a body may appear via multiple materials).
5) Selecting all visible surface sources.
6) Creating an Interactive Simulation with a **unique name**. If the base name
   is already taken by any object, the script appends _1, _2, ... or a random
   suffix to avoid conflicts.
"""

# =============================================================================
# Configuration
# =============================================================================
REQUIRE_VISIBLE = False  # Set to True to include only visible bodies

# =============================================================================
# Helper Functions
# =============================================================================
def ensure_body_docobject(dobj):
    """
    Resolve any linked Speos or SpaceClaim object to its owning DesignBody
    and return a document-level object (IDocObject) suitable for simulation.

    This function promotes lower-level geometry references (faces, features,
    or temporary links) to their parent DesignBody, ensuring that only
    complete physical bodies are passed to the simulation.

    Parameters
    ----------
    dobj : object
        A linked Speos or SpaceClaim object, possibly a FaceStub, Feature, or
        another entity that belongs to a DesignBody.

    Returns
    -------
    IDocObject
        The DesignBody document object if found; otherwise the input object.

    Notes
    -----
    - Speos materials often reference faces or features instead of full bodies.
      Passing those directly to the simulation can create anonymous “Solid”
      entries or duplicate geometry.
    - This function uses several fallback strategies (.Root, .GetDocObject(),
      .GetBody()) to climb back to the owning DesignBody.
    - If resolution fails, the original object is returned so that
      `Selection.Create()` may still normalize it automatically.

    Examples
    --------
    >>> body = ensure_body_docobject(face_stub)
    >>> print(body.GetName())
    'Body - Light Guide'
    """
    # 1) Already a body-level docobject
    if hasattr(dobj, "GetName") and hasattr(dobj, "IsVisible"):
        return dobj

    # 2) Try GetDocObject() and its Root
    if hasattr(dobj, "GetDocObject"):
        try:
            doc = dobj.GetDocObject()
            if doc is not None:
                if hasattr(doc, "IsVisible") and hasattr(doc, "GetName"):
                    return doc
                root = getattr(doc, "Root", None)
                if root is not None and hasattr(root, "IsVisible") and hasattr(root, "GetName"):
                    return root
        except Exception as e: 
    print("Exception found: " + str(e))

    # 3) Try Root directly
    root = getattr(dobj, "Root", None)
    if root is not None:
        if hasattr(root, "IsVisible") and hasattr(root, "GetName"):
            return root
        if hasattr(root, "GetDocObject"):
            try:
                bdoc = root.GetDocObject()
                if bdoc is not None and hasattr(bdoc, "IsVisible") and hasattr(bdoc, "GetName"):
                    return bdoc
            except Exception as e: 
    print("Exception found: " + str(e))

    # 4) Try GetBody() fallback
    if hasattr(dobj, "GetBody"):
        try:
            b = dobj.GetBody()
            if b is not None:
                if hasattr(b, "GetDocObject"):
                    bd = b.GetDocObject()
                    if bd is not None and hasattr(bd, "IsVisible") and hasattr(bd, "GetName"):
                        return bd
                if hasattr(b, "IsVisible") and hasattr(b, "GetName"):
                    return b
        except Exception as e: 
    print("Exception found: " + str(e))

    # Fallback: return as-is
    return dobj


def docobject_idkey(dobj):
    """
    Build a stable unique key for a document object to enable deduplication.

    This function extracts a consistent identifier from a SpaceClaim/Speos
    document object (IDocObject) using the following priority:
    ReferenceId > Id > Name > repr().

    Parameters
    ----------
    dobj : IDocObject
        The document object to generate an identifier for.

    Returns
    -------
    tuple
        A (type, string) tuple usable as a hashable key in a set or dict.

    Notes
    -----
    Deduplication avoids adding the same geometry multiple times when materials
    overlap (e.g., volumic + surfacic on one body).

    Examples
    --------
    >>> key = docobject_idkey(my_body)
    >>> print(key)
    ('ref', '123456')
    """
    rid = getattr(dobj, "ReferenceId", None)
    if rid:
        return ("ref", str(rid))
    oid = getattr(dobj, "Id", None)
    if oid:
        return ("id", str(oid))
    try:
        return ("name", dobj.GetName())
    except:
        return ("obj", repr(dobj))


def is_visible_safe(dobj):
    """
    Safely check whether a geometry or document object is visible in the model.

    This function wraps `dobj.IsVisible(None)` in a try/except block to prevent
    crashes when an object does not expose a valid visibility property (common
    with certain Speos or SpaceClaim linked objects). If the check fails, it
    returns True by default.

    Parameters
    ----------
    dobj : IDocObject or similar
        The object whose visibility is being queried.

    Returns
    -------
    bool
        True if the object is visible, or if visibility cannot be determined.
        False only if the object explicitly reports invisibility.

    Notes
    -----
    The function defaults to True on error to avoid excluding valid bodies from
    the simulation in ambiguous cases.

    Examples
    --------
    >>> is_visible_safe(body)
    True
    """
    try:
        return dobj.IsVisible(None)
    except:
        return True  # Be permissive if uncertain


def assign_unique_name(target_obj, base_name, max_seq=100):
    """
    Assign a unique name to a Speos/SpaceClaim object.

    The function first tries the base name. If it is already taken by any
    object, it attempts base_name_1, base_name_2, ..., up to `max_seq`.
    If all those fail (name collision or API rejection), it appends a random
    6-hex suffix to guarantee uniqueness.

    Parameters
    ----------
    target_obj : object
        The object whose `Name` attribute will be set.
    base_name : str
        Desired base name (e.g., "Raytracing of Visible Elements").
    max_seq : int, optional
        Maximum integer suffix to try before switching to a random suffix.

    Returns
    -------
    str
        The name that was successfully assigned to the object.

    Notes
    -----
    - Some environments reject a name if *any* other object in the document
      uses it (not only simulations). Hence we try/except on the setter.
    - This is robust in IronPython (no f-strings). It uses old-style formatting.

    Examples
    --------
    >>> name = assign_unique_name(interactive, "Raytracing of Visible Elements")
    >>> print(name)
    'Raytracing of Visible Elements_2'
    """
    # 1) Try the base name directly
    try:
        target_obj.Name = base_name
        return target_obj.Name
    except:
        pass

    # 2) Try numbered suffixes
    i = 1
    while i <= max_seq:
        trial = "%s_%d" % (base_name, i)
        try:
            target_obj.Name = trial
            return target_obj.Name
        except:
            i += 1

    # 3) Fallback: random short suffix
    try:
        import uuid
        trial = "%s_%s" % (base_name, uuid.uuid4().hex[:6].upper())
        target_obj.Name = trial
        return target_obj.Name
    except:
        # Last resort: keep incrementing until one works
        j = max_seq + 1
        while True:
            trial = "%s_%d" % (base_name, j)
            try:
                target_obj.Name = trial
                return target_obj.Name
            except:
                j += 1


# =============================================================================
# Main Script
# =============================================================================
root = GetRootPart()

print("Total bodies in root:", root.GetAllBodies().Count)

# 1) Collect all Speos materials
material_list_names = [
    obj.GetName() for obj in root.CustomObjects
    if obj.Type == "SPEOS_SC.SIM.SpeosWrapperMaterial"
]
print("Speos materials found:", material_list_names)

# 2) Collect all geometries linked to those materials
candidate_doc_bodies = []

for material_name in material_list_names:
    m = SpeosSim.Material.Find(material_name)
    if m is None:
        print("WARNING: Material not found:", material_name)
        continue

    opt_type = str(m.OpticalPropertiesType)
    print("\nMaterial:", material_name, "| OpticalPropertiesType:", opt_type)

    if opt_type == "Volumic":
        linked = list(m.VolumeGeometries.LinkedObjects)
        print("  VolumeGeometries.LinkedObjects:", len(linked))
        for dobj in linked:
            body_dobj = ensure_body_docobject(dobj)
            candidate_doc_bodies.append(body_dobj)

    elif opt_type == "Surfacic":
        linked = list(m.OrientedFaces.LinkedObjects)
        print("  OrientedFaces.LinkedObjects:", len(linked))
        for face_dobj in linked:
            body_dobj = ensure_body_docobject(face_dobj)
            candidate_doc_bodies.append(body_dobj)

print("\nCandidate doc bodies BEFORE filtering:", len(candidate_doc_bodies))

# 3) Optional visibility filter
if REQUIRE_VISIBLE:
    candidate_doc_bodies = [d for d in candidate_doc_bodies if is_visible_safe(d)]
    print("After visibility filter:", len(candidate_doc_bodies))
else:
    print("Visibility filter DISABLED")

# 4) Deduplicate
seen = set()
unique_doc_bodies = []
for d in candidate_doc_bodies:
    key = docobject_idkey(d)
    if key not in seen:
        seen.add(key)
        unique_doc_bodies.append(d)

print("Unique bodies to simulate:", len(unique_doc_bodies))
for d in unique_doc_bodies:
    try:
        print(" -", d.GetName())
    except:
        print(" - <unnamed body>")

# 5) Collect visible Speos surface sources
visible_source_docobjects = []
for obj in root.CustomObjects:
    if obj.Type == "SPEOS_SC.SIM.SpeosWrapperSourceSurface":
        src = SpeosSim.SourceSurface.Find(obj.GetName())
        if src is not None and src.Visible:
            visible_source_docobjects.append(obj)

print("\nVisible surface sources (count):", len(visible_source_docobjects))
for obj in visible_source_docobjects:
    try:
        print(" -", obj.GetName())
    except:
        pass

# 6) Build and configure Interactive Simulation (with guaranteed unique name)
base_sim_name = "Raytracing of Visible Elements"
interactive = SpeosSim.SimulationInteractive.Create()
final_name = assign_unique_name(interactive, base_sim_name)
print("Created simulation with name:", final_name)

if len(unique_doc_bodies) > 0:
    sel_geos = Selection.Create(unique_doc_bodies)
    print("Selection.Create for geometries -> Items:", sel_geos.Count)
    interactive.Geometries.Set(sel_geos.Items)
else:
    print("WARNING: No bodies found to assign to the simulation geometries.")

if len(visible_source_docobjects) > 0:
    sel_src = Selection.Create(visible_source_docobjects)
    print("Selection.Create for sources -> Items:", sel_src.Count)
    interactive.Sources.Set(sel_src.Items)
else:
    print("WARNING: No visible surface sources found to assign.")

# 7) Run (optional)
# interactive.Compute()

print("\nInteractive simulation prepared:", interactive.Name)
