"""A collection of cutie-specific calls for post-hoc- and live-processing."""

import os

import torch
from torchvision.transforms.functional import to_tensor
from PIL import Image
import numpy as np
from pathlib import Path

from cutie.inference.inference_core import InferenceCore

from omegaconf import open_dict
from hydra import compose, initialize_config_dir, initialize
from cutie.model.cutie import CUTIE

# cutie uses the davis_palette
davis_palette = b'\x00\x00\x00\x80\x00\x00\x00\x80\x00\x80\x80\x00\x00\x00\x80\x80\x00\x80\x00\x80\x80\x80\x80\x80@\x00\x00\xc0\x00\x00@\x80\x00\xc0\x80\x00@\x00\x80\xc0\x00\x80@\x80\x80\xc0\x80\x80\x00@\x00\x80@\x00\x00\xc0\x00\x80\xc0\x00\x00@\x80\x80@\x80\x00\xc0\x80\x80\xc0\x80@@\x00\xc0@\x00@\xc0\x00\xc0\xc0\x00@@\x80\xc0@\x80@\xc0\x80\xc0\xc0\x80\x00\x00@\x80\x00@\x00\x80@\x80\x80@\x00\x00\xc0\x80\x00\xc0\x00\x80\xc0\x80\x80\xc0@\x00@\xc0\x00@@\x80@\xc0\x80@@\x00\xc0\xc0\x00\xc0@\x80\xc0\xc0\x80\xc0\x00@@\x80@@\x00\xc0@\x80\xc0@\x00@\xc0\x80@\xc0\x00\xc0\xc0\x80\xc0\xc0@@@\xc0@@@\xc0@\xc0\xc0@@@\xc0\xc0@\xc0@\xc0\xc0\xc0\xc0\xc0 \x00\x00\xa0\x00\x00 \x80\x00\xa0\x80\x00 \x00\x80\xa0\x00\x80 \x80\x80\xa0\x80\x80`\x00\x00\xe0\x00\x00`\x80\x00\xe0\x80\x00`\x00\x80\xe0\x00\x80`\x80\x80\xe0\x80\x80 @\x00\xa0@\x00 \xc0\x00\xa0\xc0\x00 @\x80\xa0@\x80 \xc0\x80\xa0\xc0\x80`@\x00\xe0@\x00`\xc0\x00\xe0\xc0\x00`@\x80\xe0@\x80`\xc0\x80\xe0\xc0\x80 \x00@\xa0\x00@ \x80@\xa0\x80@ \x00\xc0\xa0\x00\xc0 \x80\xc0\xa0\x80\xc0`\x00@\xe0\x00@`\x80@\xe0\x80@`\x00\xc0\xe0\x00\xc0`\x80\xc0\xe0\x80\xc0 @@\xa0@@ \xc0@\xa0\xc0@ @\xc0\xa0@\xc0 \xc0\xc0\xa0\xc0\xc0`@@\xe0@@`\xc0@\xe0\xc0@`@\xc0\xe0@\xc0`\xc0\xc0\xe0\xc0\xc0\x00 \x00\x80 \x00\x00\xa0\x00\x80\xa0\x00\x00 \x80\x80 \x80\x00\xa0\x80\x80\xa0\x80@ \x00\xc0 \x00@\xa0\x00\xc0\xa0\x00@ \x80\xc0 \x80@\xa0\x80\xc0\xa0\x80\x00`\x00\x80`\x00\x00\xe0\x00\x80\xe0\x00\x00`\x80\x80`\x80\x00\xe0\x80\x80\xe0\x80@`\x00\xc0`\x00@\xe0\x00\xc0\xe0\x00@`\x80\xc0`\x80@\xe0\x80\xc0\xe0\x80\x00 @\x80 @\x00\xa0@\x80\xa0@\x00 \xc0\x80 \xc0\x00\xa0\xc0\x80\xa0\xc0@ @\xc0 @@\xa0@\xc0\xa0@@ \xc0\xc0 \xc0@\xa0\xc0\xc0\xa0\xc0\x00`@\x80`@\x00\xe0@\x80\xe0@\x00`\xc0\x80`\xc0\x00\xe0\xc0\x80\xe0\xc0@`@\xc0`@@\xe0@\xc0\xe0@@`\xc0\xc0`\xc0@\xe0\xc0\xc0\xe0\xc0  \x00\xa0 \x00 \xa0\x00\xa0\xa0\x00  \x80\xa0 \x80 \xa0\x80\xa0\xa0\x80` \x00\xe0 \x00`\xa0\x00\xe0\xa0\x00` \x80\xe0 \x80`\xa0\x80\xe0\xa0\x80 `\x00\xa0`\x00 \xe0\x00\xa0\xe0\x00 `\x80\xa0`\x80 \xe0\x80\xa0\xe0\x80``\x00\xe0`\x00`\xe0\x00\xe0\xe0\x00``\x80\xe0`\x80`\xe0\x80\xe0\xe0\x80  @\xa0 @ \xa0@\xa0\xa0@  \xc0\xa0 \xc0 \xa0\xc0\xa0\xa0\xc0` @\xe0 @`\xa0@\xe0\xa0@` \xc0\xe0 \xc0`\xa0\xc0\xe0\xa0\xc0 `@\xa0`@ \xe0@\xa0\xe0@ `\xc0\xa0`\xc0 \xe0\xc0\xa0\xe0\xc0``@\xe0`@`\xe0@\xe0\xe0@``\xc0\xe0`\xc0`\xe0\xc0\xe0\xe0\xc0'
davis_palette_np = np.frombuffer(davis_palette, dtype=np.uint8).reshape(-1, 3)
davis_palette_1d = list(davis_palette_np.reshape(-1,))  
# cutie_pallette is the same 1D list as mask.getpalette() in the scripting_demo.py
# [[  0   0   0],  [128   0   0],  [  0 128   0],  [128 128   0]
# davis_alpha_channel = np.zeros((davis_palette_np.shape[0],1))
# davis_palette_np = np.concatenate((davis_palette_np, davis_alpha_channel), axis=-1)

processor:InferenceCore = None

def download_models_if_needed(weight_dir:str='./cutie_weights') -> str:
    """modified from cutie/utils/download_models.py"""
    import requests
    from tqdm import tqdm
    import hashlib
    link, md5 = 'https://github.com/hkchengrex/Cutie/releases/download/v1.0/cutie-base-mega.pth', 'a6071de6136982e396851903ab4c083a'
    os.makedirs(weight_dir, exist_ok=True)
    # download file if not exists with a progressbar
    filename = link.split('/')[-1]
    if not os.path.exists(os.path.join(weight_dir, filename)) or hashlib.md5(open(os.path.join(weight_dir, filename), 'rb').read()).hexdigest() != md5:
        print(f'Downloading {filename} to {weight_dir}...')
        r = requests.get(link, stream=True)
        total_size = int(r.headers.get('content-length', 0))
        block_size = 1024
        t = tqdm(total=total_size, unit='iB', unit_scale=True)
        with open(os.path.join(weight_dir, filename), 'wb') as f:
            for data in r.iter_content(block_size):
                t.update(len(data))
                f.write(data)
        t.close()
        if total_size != 0 and t.n != total_size:
            raise RuntimeError('Error while downloading %s' % filename)
    return weight_dir

def create_cutie(cutie_config_path:str|Path, config_name='gui_config'):
    """
    Initialize and configure a cutie instance for video/live object segmentation. The model will 
    automatically be downloaded into a folder ./cutie_weights if not already existing.
    
    Args:
        cutie_config_path (str|Path): Path to the CUTIE configuration file. Can be absolute or relative.
        config_name (str, optional): Name of the configuration to load. Defaults to 'gui_config' to load
        gui_config.yml from the cutie_config_path."""

    # in the future the cutie install's config path could be automatically found/used and a local config be
    # copied into it if provided instead of the default eval_config
    global processor
    """modified from cutie/utils/get_default_mode.py"""
    if Path(cutie_config_path).is_absolute():
        initialize_config_dir(config_dir=cutie_config_path, version_base='1.3.2', job_name=config_name)
    else:
        initialize(config_path=cutie_config_path, version_base='1.3.2', job_name=config_name)
    cfg = compose(config_name=config_name)

    download_models_if_needed(weight_dir='./cutie_weights')
    with open_dict(cfg):
        cfg['weights'] = './cutie_weights/cutie-base-mega.pth'

    # Load the network weights
    cutie = CUTIE(cfg).cuda().eval()
    model_weights = torch.load(cfg.weights)
    cutie.load_weights(model_weights)

    processor = InferenceCore(cutie, cfg=cutie.cfg)
    # print(f'using cutie configuration:\n{cutie.cfg}')

@torch.inference_mode()
@torch.amp.autocast('cuda')
def load_references(reference_folder:str|Path):
    """
    Load reference images and their corresponding masks from a specified folder.
    
    This function loads .jpg images and .png masks as pairs from the given reference folder,
    processes and commits them to cutie's memory. Run this function before predict_folder 
    or predict_frame to have cutie continue tracking from once selected data.
    Cuties interactive_demo.py allows easy creation of image/mask pairs which can then be
    gathered as jpg/png files from the Cutie/workspace folder corresponding to your used video.
    Choose frames that reflect the range of situations your tracking targets can be found in well.
    The more complex your tracked elements the more frames will be needed in combination with a more 
    long-term focused configuartion.
    
    Args:
        reference_folder (str|Path): Path to the folder containing reference images (.jpg)
                                     and masks (.png). The folder should contain an equal
                                     number of .jpg and .png files with equal names before
                                     their file type, i.e. 0001779.jpg and 0001779.png.
    """
    global processor
    reference_folder = Path(reference_folder)
    
    images = list(reference_folder.glob('*.jpg'))
    masks = list(reference_folder.glob('*.png'))

    if len(images) != len(masks):
        print(f'number of .jpg and .png files does not match ({len(images)} vs {len(masks)}), please ensure that your reference masks match your references images. No references were loaded')
        return
    
    for i in range(len(images)):
        print(f'cutie processing reference image {i}')
        image = Image.open(images[i])
        image = to_tensor(image).cuda().float()
        mask = Image.open(masks[i])
        assert mask.mode in ['P', 'L'] # P Palette mappable color indices 0, 1, 2

        objects = np.unique(np.array(mask))
        # background "0" does not count as an object
        objects = objects[objects != 0].tolist()

        mask = torch.from_numpy(np.array(mask)).cuda()
        # if a mask is passed to processor.step(), it is memorized.
        # if not all objects are specified, we propagate the unspecified objects using memory
        output_prob = processor.step(image, mask, objects=objects)

@torch.inference_mode()
@torch.amp.autocast('cuda')
def predict_folder(image_folder:str, mask_output_folder:str, first_file_idx:int=0):
    global processor, davis_palette_1d

    images = sorted(os.listdir(image_folder))

    for i in range(first_file_idx, len(images)):
        image = Image.open(os.path.join(image_folder, images[i]))
        image = to_tensor(image).cuda().float() # shape = [3, 720, 1280]
        
        # we propagate the mask using memory
        output_prob = processor.step(image)
        # convert output probabilities to an object mask
        mask = processor.output_prob_to_mask(output_prob)

        # Create a 2d array with idxs for objects, i.e. 0 = background, 1 = 1st object, 2 = 2nd object
        mask_indices = mask.cpu().numpy().astype(np.uint8)
        # map indices to colors (PIL pallette is a bit faster than numpy approach)
        colored = Image.fromarray(mask_indices) 
        colored.putpalette(davis_palette_1d)
        colored.save(f'{mask_output_folder}/{i:07d}.png') 
        print(f'processed frame {i}')

@torch.inference_mode()
@torch.amp.autocast('cuda')
def predict_frame(frame:np.ndarray, apply_pallete=False) -> tuple[np.ndarray, np.ndarray]:
    global processor
    image = torch.Tensor(frame).cuda().float()
    # turn the image from color channel last to color channel first, i.e. [480, 640, 3] to [3, 480, 640]
    image = image.permute(2, 0, 1)
    image = image / 256
    # values line up to example data format with numpy test and result in a correct prediction 

    output_prob = processor.step(image)
    masks = processor.output_prob_to_mask(output_prob)
    # Create a 2d array with idxs for objects, i.e. 0 = background, 1 = 1st object, 2 = 2nd object
    masks = masks.cpu().numpy().astype(np.uint8)

    if apply_pallete:
        masks = davis_palette_np[masks]

    return frame, masks

from scipy import ndimage
import json

def calculate_center_of_mass(masks_folder):
    positions = {}
    mask_files = sorted(os.listdir(masks_folder))
    for i, image_name in enumerate(mask_files):
        mask = np.asarray(Image.open(masks_folder + '\\' + image_name))
        if i % 100 == 0:
            print(i)
        # plt.imshow(mask)
        # plt.show()
        
        center_of_mass = ndimage.center_of_mass(mask) # y, x
        if np.isnan(center_of_mass[0]):
            positions[i] = None
            print('lost')
        else:
            positions[i] = center_of_mass
        
    with open('centers_of_mass.json', 'w') as f:
        json.dump(positions, f, indent=2)