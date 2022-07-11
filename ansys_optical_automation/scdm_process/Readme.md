### Functionality
The class ``MaterialsFromCSV`` has methods to:
 
 - Create Speos materials specified in the CSV file ``Materials.csv``
 - Create SpaceClaim layers with the same names as the Speos material
 - Assign created materials to the geometries, if the geometry ``property`` field is equal to the material name.
 - Aassign geometries to the SpaceClaim layers based on the Speos material name.

### Example usage:
Your script should import the ``MaterialsFromCSV`` class: 

    import sys
    sys.path.append("D:\\optical-automation")
    
    from ansys_optical_automation.scdm_process.materal_from_csv import MaterialsFromCSV
    
    csv_path = "D:\\#ANSYS SPEOS_Concept Proof\\API Scripts\\ASP_MaterialFromCsv\\Materials.csv"
    work_directory = "D:\\#ANSYS SPEOS_Concept Proof\\API Scripts\\ASP_MaterialFromCsv\\"

    MatWizard = MaterialsFromCSV(SpeosSim, SpaceClaim)
    MatWizard.create_speos_material(csv_path, work_directory)
    MatWizard.apply_geo_to_material()
    MatWizard.apply_geo_to_layer()
