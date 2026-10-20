import yaml
import pathlib

class Configurator():
    CHECKERBOARD = "checkerboard"
    STEREO_CAMERA = "stereo_camera"
    MONOCULAR_CAMERA = "monocular_camera"
    CALIBRATOR = "calibrator"
    
    def __init__(self, pkg: str = None):
        self.__configFile = ''
        self.__pkg = pkg
    
    @staticmethod
    def getProjectRoot():
        # Both markers are required: package dirs may also hold a config/ folder.
        current = pathlib.Path(__file__).resolve()
        for parent in current.parents:
            if (parent / 'config').is_dir() and (parent / 'src').is_dir():
                return str(parent)
        raise FileNotFoundError("Could not find project root with /config and /src directories")

    def __getConfigDir(self):
        project_root = Configurator.getProjectRoot()
        if self.__pkg is None:
            return f"{project_root}/config"
        return f"{project_root}/src/{self.__pkg}/config"
    def __raiseTypeError(self,data_type):
        consts = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("_")]
        raise TypeError(f"Config file of type {data_type} doesn't exist, only {', '.join(consts)} are allowed.")
    
    def getConfigsNames(self):
        consts = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("_")]
        return [getattr(self, attr) for attr in consts]

    def __getYamlFile(self, data_type):
        config_dir = self.__getConfigDir()
        config_filename = None
        
        if data_type == Configurator.CHECKERBOARD:
            config_filename = Configurator.CHECKERBOARD
        elif data_type == Configurator.STEREO_CAMERA:
            config_filename = Configurator.STEREO_CAMERA
        elif data_type == Configurator.MONOCULAR_CAMERA:
            config_filename = Configurator.MONOCULAR_CAMERA
        elif data_type == Configurator.CALIBRATOR:
            config_filename = Configurator.CALIBRATOR
        else:
            self.__raiseTypeError(data_type)
        
        if config_filename:
            self.__configFile = f"{config_dir}/{config_filename}.yaml"
    def fetchData(self,data_type):
        try:
            self.__getYamlFile(data_type)
            with open(self.__configFile, 'r') as file:
                data = yaml.safe_load(file)
                return data
        except FileNotFoundError:
            print(f"Error: The file '{self.__configFile}' was not found.")
        except yaml.YAMLError:
            print("Error: Failed to parse the YAML file.")
        except TypeError as e:
            print(e)
    def setConfig(self, data_type, new_data):
        """
        Update the YAML configuration file with new_data.
        Only updates the keys provided in new_data and keeps other keys intact.

        :param data_type: Type of configuration (e.g., "cameras", "joystick_buttons")
        :param new_data: Dictionary containing the new key-value pairs to update.
        """
        try:
            self.__getYamlFile(data_type)

            # Load existing data
            try:
                with open(self.__configFile, 'r') as file:
                    existing_data = yaml.safe_load(file) or {}  # Handle empty file case
            except FileNotFoundError:
                existing_data = {}
                print(f"Warning: {self.__configFile} not found. A new file will be created.")

            # Update existing data with new_data (merge dictionaries)
            updated_data = {**existing_data, **new_data}

            # Write back to file
            with open(self.__configFile, 'w') as file:
                yaml.safe_dump(updated_data, file, default_flow_style=False)

            print(f"Configuration for '{data_type}' updated successfully.")

        except FileNotFoundError:
            print(f"Error: The directory for '{self.__configFile}' was not found.")
        except yaml.YAMLError as e:
            print(f"Error: Failed to write YAML data. Details: {e}")
        except TypeError as e:
            print(e)