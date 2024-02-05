# %%
import os
import pandas as pd
from datetime import date
from shutil import copy as cpy
import re

import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account

# %%
today = date.today().strftime("%Y-%m-%d")
post_path ='../posts'
path = os.path.join(post_path, today)

os.makedirs(path, 0o755, True)

# %%


# %%
def convert_google_sheet_url(url):
    # Regular expression to match and capture the necessary part of the URL
    pattern = r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?'

    # Replace function to construct the new URL for CSV export
    # If gid is present in the URL, it includes it in the export URL, otherwise, it's omitted
    replacement = lambda m: f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?' + (f'gid={m.group(3)}&' if m.group(3) else '') + 'format=csv'

    # Replace using regex
    new_url = re.sub(pattern, replacement, url)

    return new_url

# %%
# Replace with your modified URL
url = 'https://docs.google.com/spreadsheets/d/1bJIUEOh8yUg46dREnE_bXlha9K35nqkFk85CyQYn2eY/edit#gid=932148422'

new_url = convert_google_sheet_url(url)

df = pd.read_csv(new_url)

# %%
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

SERVICE_ACCOUNT_FILE =  "/root/afromation-key.json"


def get_authenticated_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

# %%
creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

# %%
youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

# %%
video_meta = []
video_id  = []

def main(channelID):
    request = youtube.search().list(
        part='snippet',
        # id="UC12lU5ymIvSpgl8KntDQUQA"
        channelId=channelID,
        order="date",
        type="video",
        maxResults=1
    )

    response = request.execute()

    snippet = response['items'][0]['snippet']
    videoid = response['items'][0]['id']['videoId']
    video_meta.append(snippet)
    video_id.append(videoid)


#df  = pd.read_csv('youTubeChannels.csv')

#df[['id', 'Creator', 'Category']]
#channels = ['UC12lU5ymIvSpgl8KntDQUQA']

channels = df['id']


if __name__ == "__main__":
    for chan in channels:
        main(chan)

# %%
meta = pd.DataFrame.from_dict(video_meta)
video_meta_df = meta.assign(videoID = video_id)


# %%
video  = []

def main(id):
    request = youtube.videos().list(
        part="player",
        id=id
    )

    response = request.execute()

    video.append(response['items'])



#df[['id', 'Creator', 'Category']]
# channels = ['jh4ln6QcYVE']

vids = video_meta_df['videoID']


if __name__ == "__main__":
    for vid in vids:
        main(vid)

# %%
embed_codes = [item[0]['player']['embedHtml'] for item in video]


# %%
meta = pd.DataFrame.from_dict(video_meta)
video_meta_df = meta.assign(videID = video_id,
                            embeds = embed_codes)
video_meta_df = video_meta_df.sort_values(by=['publishedAt'], ascending=False)
video_meta_df.to_csv(os.path.join(path, 'videos_tbl.csv'))
video_meta_df

# %%
today_title = date.today().strftime("%b %d, %Y")
samples     = video_meta_df['title'][0:5]
subtitles   = ['; '.join(samples[0 : 5])]

# %%
markdown_content = f"""
---
date: {today}
title: 'Daily Update – {today_title}'
format: 
    html:
      toc: false
title-block-banner: true
execute:
    echo: false
    warning: false
    message: false
---
'{subtitles[0]}'

```{{r}}

library(tidyverse)
googlesheets4::gs4_deauth()
sheet <- googlesheets4::read_sheet('https://docs.google.com/spreadsheets/d/1bJIUEOh8yUg46dREnE_bXlha9K35nqkFk85CyQYn2eY/edit#gid=932148422',
                                   sheet =  'YouTube Channels')

videos_tbl <- read_csv('videos_tbl.csv') |> 
  mutate(embeds = embeds |> 
           str_replace_all('480', '100%') |> 
           str_replace_all('270', '400'))

```

```{{r}}
#| echo: false

# A list of summaries:

 
videos_joined <- videos_tbl |> 
    left_join(sheet, by = join_by(channelId == id)) |> 
    select(publishedAt,title, description, embeds, 
           channelId, Category) |> 
    filter(publishedAt >= lubridate::today()-1)

videos <- videos_joined |>  
    split(videos_joined$Category) 
    

headings <- names(videos)
#videos
```

## Today's Videos

::: panel-tabset
```{{r, results='asis'}}
#| warning: false


for (i in seq_along(videos)) {{
    cat("# ",headings[i],"\\n")
    current_df <- videos[[i]]
  
    
    for (j in seq_along(current_df$embeds)) {{
        current_value <- current_df$embeds[j]
        
        current_title <- current_df$title[j]
        cat("### ",current_title,"\\n")
        cat(current_value)
        cat("\\n")
        cat("\\n") 
         
         
         
 }}
}}
```
:::
"""

# Save to a Markdown file
file_name = os.path.join(path,'index.qmd')
with open(file_name, "w", encoding="utf-8") as file:
    file.write(markdown_content)


