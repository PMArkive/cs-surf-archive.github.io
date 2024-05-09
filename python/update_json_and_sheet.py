import json
import config
import os
import set_sheet_data

# variables set strictly for visibility and readability

MISSING_SCREENSHOT_ID = config.MISSING_SCREENSHOT_ID

SHEET_DATA = config.get_sheet_data_from_json()
SCREENSHOTS_DATA = config.get_screenshot_data_from_json()
MAPS_DATA = config.get_map_data_from_json()

MAP_NAME_INDEX = config.get_map_name_index()
SCREENSHOT_INDEX = config.get_screenshot_index()
MAP_DOWNLOAD_INDEX = config.get_map_download_index()
JUMP_LINK_INDEX = config.get_jump_link_index()

SHEET_DATA_FILE_POST_PROCESSING = config.SHEET_DATA_FILE_POST_PROCESSING

# if a sheet item doesn't have a download id or screenshot id, it won't have as many items in its entry as the header column
# so the indexes we got above will be pointing to indexes that don't exist in the item for that map's json
# so we gotta pad it with empty values, so it can write.

def pad_rows():
    max_len = len(SHEET_DATA[0])

    for row in SHEET_DATA[1:]:
        diff = max_len - len(row)
        if diff > 0:
            row += [""] * diff
    print("pad_rows function updated sheet with padded rows")

# simple helper to strip .jpg or .bsp or .png or whatever else after the . in an id from json
def split_filename_and_extension(filename):
    filename = os.path.splitext(filename)[0]
    file_extension = os.path.splitext(filename)[1]
    return filename, file_extension

def build_formatted_map_link_from_id(map_id, map_name):
    # builds the map link as the website expects it fom the id
    drive_link = f"https://drive.google.com/file/d/{map_id}/view?usp=share_link"
    formatted_site_link = f'<a href="{drive_link}">{map_name}.zip</a>' # don't feel like calling drive api every time to get file type.  it's always zip for downloads
    return formatted_site_link

def build_formatted_screenshot_link_from_id(screenshot_id, map_name):
    # builds the screenshot link as the website expects it from the id  
    # https://lienuc.com/ - Jan 2024 google broke how embeds worked
    # so, strip IDs from full URL (item) and run through lienuc
    lienuc_image_url = f'crossorigin="anonymous" src="http://drive.lienuc.com/uc?id={screenshot_id}"'  
    img_alt = f'{map_name}'
    formatted_screenshot_link = f'<img {lienuc_image_url} alt="{img_alt}" class="ImgThumbnail" loading="lazy">'
    return formatted_screenshot_link

def build_formatted_jump_link(map_name):
    # builds the jump link as the website expects it from the map name
    formatted_jump_link = (f'<b>site link:</b><br />&emsp;<a href="#{map_name}">{map_name}</a>')
    return formatted_jump_link

def match_screenshots_and_downloads_to_sheet():
    maps_with_download_but_no_screenshot =[]

    for item in SHEET_DATA[1:]:
        map_name_from_sheet, _ = split_filename_and_extension(item[MAP_NAME_INDEX])
        
        # Search for a match in SCREENSHOTS_DATA
        for screenshot in SCREENSHOTS_DATA:
            screenshot_name, _ = split_filename_and_extension(screenshot['name']) 
            if screenshot_name.lower() == map_name_from_sheet.lower():
                item[SCREENSHOT_INDEX] = build_formatted_screenshot_link_from_id(screenshot['id'], map_name_from_sheet)
                break

        # Search for a match in MAPS_DATA
        for map_item in MAPS_DATA:
            map_name_from_drive, _ = split_filename_and_extension(map_item['name'])
            if map_name_from_drive.lower() == map_name_from_sheet.lower():
                item[MAP_DOWNLOAD_INDEX] = build_formatted_map_link_from_id(map_item['id'], map_name_from_sheet)
                break

        # now that both maps and screenshots have been written,
        # look for entries of maps that have downloads but no screenshots
        # and add the missing screenshot image for both
            
        # LETS EXPLAIN THIS ONE A BIT
        # if the map download index has drive.google.com in it (meaning it has a link)
        # and the screenshot index doesn't have drive.lienuc in it (meaning there is no link)
        #   this can occur if a map is manually added
        # or the missing map ID is in the screenshot index (meaning there's already a missing screenshot link)
        #   this can occur if the sheet update code has been run
        # then we know we have a map with a download but no screenshot
        # so print about it and overwrite the cell with the missing image link
            
        if "drive.google.com" in item[MAP_DOWNLOAD_INDEX] and ("drive.lienuc" not in item[SCREENSHOT_INDEX] or MISSING_SCREENSHOT_ID in item[SCREENSHOT_INDEX]):
            item[SCREENSHOT_INDEX] = build_formatted_screenshot_link_from_id(MISSING_SCREENSHOT_ID, item[MAP_NAME_INDEX])
            maps_with_download_but_no_screenshot.append(item[MAP_NAME_INDEX])
        elif "drive.google.com" not in item[MAP_DOWNLOAD_INDEX]:
            item[SCREENSHOT_INDEX] = build_formatted_screenshot_link_from_id(MISSING_SCREENSHOT_ID, item[MAP_NAME_INDEX])

    print("maps with download but no screenshot: ", maps_with_download_but_no_screenshot)
    print(len(maps_with_download_but_no_screenshot), "total maps with download but no screenshot")

def add_jump_links():
    for item in SHEET_DATA[1:]:
        item[JUMP_LINK_INDEX] = (f'<b>site link:</b><br />&emsp;<a href="#{item[MAP_NAME_INDEX]}">{item[MAP_NAME_INDEX]}</a>')
    print("Added jump links")

def write_to_sheet():
    with open(SHEET_DATA_FILE_POST_PROCESSING, 'w') as f:
        json.dump(SHEET_DATA, f, indent=4)
    
    set_sheet_data.update_sheet(SHEET_DATA)

    print("Data updated and saved to", SHEET_DATA_FILE_POST_PROCESSING)

    # set_sheet_data.update_sheet(SHEET_DATA)

if __name__ == "__main__":
    pad_rows()
    match_screenshots_and_downloads_to_sheet()
    add_jump_links()
    write_to_sheet()
