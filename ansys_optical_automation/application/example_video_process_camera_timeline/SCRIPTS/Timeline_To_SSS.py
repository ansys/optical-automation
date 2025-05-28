import yaml
import os
import re

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


wdir  = r"D:\your\working\folder_directory"
yaml_path = 'D:\your\SSS\Inputs.yaml'

def File_Counter(yaml_path, wdir):
    # Load the YAML file
    with open(yaml_path, 'r') as file:
        inputs = yaml.load(file, Loader=yaml.FullLoader)

    # Retrieve default values
    default_data = {}
    default_data['default_exposureMap'] = inputs['Given files']['Set 0']['Exposure maps']
    default_data['default_sensor'] = inputs['Given files']['Set 0']['Sensor']
    default_data['default_processedExport'] = inputs['Given files']['Set 0']['Processed export']
    default_data['default_outputfolder'] = inputs['Given files']['Set 0']['Output folder']
    print(default_data['default_exposureMap'])
    print(default_data['default_sensor'])
    print(default_data['default_processedExport'])
    
    base_key = 'Set '
    for dirpath, dirs, files in os.walk(wdir):
        for filename in files:
            fname = os.path.join(dirpath, filename)
            if fname.endswith('.xmp'):
                match = re.search(r'(\d+)', filename)
                if match:
                    index = str(int(match.group(1)))
                    # Ensure the necessary structure exists in inputs
                    inputs.setdefault('Given files', {}).setdefault(f"{base_key}{index}", {})

                    # Assign the file path and default values to the respective keys
                    inputs['Given files'][f"{base_key}{index}"]['Exposure maps'] = fname
                    inputs['Given files'][f"{base_key}{index}"]['Sensor'] = default_data['default_sensor']
                    inputs['Given files'][f"{base_key}{index}"]['Output folder'] = default_data['default_outputfolder']
                    inputs['Given files'][f"{base_key}{index}"]['Processed export'] = default_data['default_processedExport']

    # Save the modified inputs to a new YAML file
    output_yaml_path = 'D:/05-Formations/12-SSS_Importer/Training_Workshop/22-Video_Animation/Inputs_test.yaml'
    with open(output_yaml_path, 'w') as outfile:
        #yaml.safe_dump(inputs, outfile)
        yaml.dump(inputs, outfile, Dumper = NoAliasDumper)
    
File_Counter(yaml_path,wdir)

