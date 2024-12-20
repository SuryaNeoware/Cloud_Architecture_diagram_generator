# import os
# import json
# import requests

# # Base directory containing all resource folders
# base_dir = "aws_icons"  # Local directory name

# # GitHub repository details
# github_repo_user = "SuryaNeoware"
# github_repo_name = "cloud_icons"
# github_branch = "main"

# def get_github_file_url(filename):
#     # Construct GitHub raw file URL directly
#     return f"https://raw.githubusercontent.com/
#     {github_repo_user}/{github_repo_name}/{github_branch}/icon_set/aws_icons/{filename}"

# # Function to clean resource names
# def clean_resource_name(filename):
#     name = filename.rsplit(".", 1)[0]
#     return name.replace("_", " ").replace("Arch ", "").replace("Res ", "")

# # Initialize the mapping dictionary
# icon_mapping = {}

# # Walk through the base directory to find SVG files
# for root, _, files in os.walk(base_dir):
#     for file in files:
#         if file.endswith(".svg"):
#             # Get the cleaned resource name
#             resource_name = clean_resource_name(file)
            
#             # Generate the GitHub URL for the icon
#             github_url = get_github_file_url(file)
            
#             # Add the icon to the mapping dictionary
#             icon_mapping[resource_name] = [github_url]

# # Save the mappings to a single JSON file
# output_file = "aws_icon_mapping.json"
# with open(output_file, "w") as json_file:
#     json.dump(icon_mapping, json_file, indent=4)

# print(f"Icon mapping saved to {output_file}")


# import os
# import json
# import requests

# # Base directory containing all resource folders
# base_dir = "gcp_icons"  # Local directory name

# # GitHub repository details
# github_repo_user = "SuryaNeoware"
# github_repo_name = "cloud_icons"
# github_branch = "main"

# def get_github_file_url(filename):
#     # Construct GitHub raw file URL directly
#     return f"https://raw.githubusercontent.com/{github_repo_user}/{github_repo_name}/{github_branch}/icon_set/gcp_icons/svg/{filename}"

# # Function to clean resource names
# def clean_resource_name(filename):
#     name = filename.rsplit(".", 1)[0]
#     return name.replace("_", " ").replace("Arch ", "").replace("Res ", "")

# # Initialize the mapping dictionary
# icon_mapping = {}

# # Walk through the base directory to find SVG files
# for root, _, files in os.walk(base_dir):
#     for file in files:
#         if file.endswith(".svg"):
#             # Get the cleaned resource name
#             resource_name = clean_resource_name(file)
            
#             # Generate the GitHub URL for the icon
#             github_url = get_github_file_url(file)
            
#             # Add the icon to the mapping dictionary
#             icon_mapping[resource_name] = [github_url]

# # Save the mappings to a single JSON file
# output_file = "gcp_icon_mapping.json"
# with open(output_file, "w") as json_file:
#     json.dump(icon_mapping, json_file, indent=4)

# print(f"Icon mapping saved to {output_file}")


import os
import json
import urllib.parse  # Module for encoding URLs

# Base directory for Azure icons
azure_base_dir = "icons"

# GitHub repository details
github_repo_user = "SuryaNeoware"
github_repo_name = "cloud_icons"
github_branch = "main"

# Function to generate the properly encoded GitHub URL for the SVG file
def get_github_file_url(relative_path):
    # Construct the raw GitHub URL with proper encoding
    encoded_path = urllib.parse.quote(relative_path.replace("\\", "/"), safe="/")
    return f"https://raw.githubusercontent.com/{github_repo_user}/{github_repo_name}/{github_branch}/icon_set/icons/{encoded_path}"

# Function to clean resource names (optional, for better readability)
def clean_resource_name(filename):
    # Remove prefixes and "icon-service-"
    name = filename.split("-icon-service-", 1)[-1].rsplit(".", 1)[0]
    return name.replace("-", " ")

# Initialize the mapping dictionary
azure_icon_mapping = {}

# Process Azure Icons
for root, _, files in os.walk(azure_base_dir):
    for file in files:
        if file.endswith(".svg"):
            # Get the relative path to the file
            relative_path = os.path.relpath(os.path.join(root, file), azure_base_dir)
            # Clean the resource name
            resource_name = clean_resource_name(file)
            # Generate the GitHub URL for the icon
            github_url = get_github_file_url(relative_path)
            
            # Add to the mapping dictionary
            azure_icon_mapping[f"Azure {resource_name}"] = [github_url]

# Save the mappings to a JSON file
output_file = "azure_icon_mapping.json"
with open(output_file, "w") as json_file:
    json.dump(azure_icon_mapping, json_file, indent=4)

print(f"Azure icon mapping saved to {output_file}")
