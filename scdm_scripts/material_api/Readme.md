### Functionality
Class MaterialsFromCSV has methods to:
 1) create SPEOS materials specified in the csv file Materials.csv
 2) create SCDM layers with the same names as SPEOS materials
 2) assign created materials to the geometries, if the geometry "property" field is equal to the material name.
 3) assign geometries to the SCDM layers based on the SPEOS material name.

### Example usage:
Your script should import the MaterialsFromCSV class: 

    import sys
    sys.path.append("D:\\#SPEOS_Migration")
    
    from scdm_scripts.materialapi_script_migration_2021r1.MaterialFroCSV_v4 import MaterialsFromCSV
    
    csv_path = "D:\\#ANSYS SPEOS_Concept Proof\\API Scripts\\ASP_MaterialFromCsv\\Materials.csv"
    work_directory = "D:\\#ANSYS SPEOS_Concept Proof\\API Scripts\\ASP_MaterialFromCsv\\"

    MatWizard = MaterialsFromCSV(SpeosSim, SpaceClaim)
    MatWizard.create_speos_material(csv_path, work_directory)
    MatWizard.apply_geo_to_material()
    MatWizard.apply_geo_to_layer()
