from cutils import create_cutie, load_references, predict_folder

cutie_config_path =  r'C:\path\to\cloned\repository\of\Cutie\cutie\config'
reference_folder =   r'C:\path\to\folder\of\reference\imageJPGs\and\maskPNGs\pairs\created\with\cutie\interactivedemo'
image_input_folder = r'C:\path\to\folder\of\image\jpgs\to\create\masks\for'
mask_output_folder = r'C:\path\to\mask\saving\folder'

create_cutie(cutie_config_path)
load_references(reference_folder)
predict_folder(image_input_folder, mask_output_folder)
