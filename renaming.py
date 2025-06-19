import os
import glob

def remove_spaces_in_names(root_dir='.'):
    # Get all files and folders recursively
    paths = glob.glob(os.path.join(root_dir, '**'), recursive=True)

    # Sort by descending length to rename subitems before parent folders
    paths.sort(key=len, reverse=True)

    index  =1
    for path in paths:
        # Skip if there is no space in name
        # if ' ' not in os.path.basename(path):
        #     continue

        # New path without spaces
        new_path = os.path.join(os.path.dirname(path), os.path.basename(path).replace(' ', ''))

        try:
            os.rename(path, new_path.lower())
            print(f'{index}. Renamed: {path} -> {new_path}')
            index+=1
        except Exception as e:
            print(f'Error renaming {path}: {e}')

# Example usage
remove_spaces_in_names(r'static\images\portfolios')  # Replace '.' with any specific root directory
