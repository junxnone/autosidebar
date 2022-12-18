import os
import glob
import pandas as pd
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('--path', default='none')
args = ap.parse_args()

doc_ptn = os.path.join(args.path, '*.md')
file_list = glob.glob(doc_ptn)
ignore_files = ['_sidebar.md', 'NAV.md', 'README.md']

for igf in ignore_files:
    igf_path = os.path.join(args.path + igf)
    if igf_path in file_list:
        file_list.remove(igf_path)

fd = {"filepath": pd.Series(file_list)}
fdf = pd.DataFrame(fd)
fdf.filepath.str.split("/", expand=True)
fdf["filename"] = fdf.filepath.str.split("/", expand=True)[1]
namex = fdf.filename.str.split(".", expand=True)[0].rename("name0")
fdf = fdf.join(namex)

cls_df = fdf.filename.str.replace('.', '_', regex=False).str.split("_", expand=True, regex=False)
fdf = fdf.join(cls_df)
fdf.fillna(value="None", inplace=True)

def search_sort_cls(df, level):
    cls_list = df[level].value_counts().index.tolist()
    if "None" in cls_list:
        cls_list.remove("None")
    if "" in cls_list:
        cls_list.remove("")
    return cls_list

fdf['link'] = '[' + fdf.name0.str.replace('_', ' ') + '](/' + fdf.name0 + ')'
def loop_cls(ldf, nloop, maxloop):
    list_0 = search_sort_cls(ldf, nloop)
    for cls0n in list_0:
        #print(cls0n)
        cls0_df = ldf[ldf[nloop] == cls0n]
        #print(ldf)
        for ll in cls0_df[cls0_df[nloop+1] == 'md'].link:
            print((' ' * nloop * 2) + (f'- {ll}'))
        if nloop < maxloop:
            loop_cls(cls0_df, nloop+1, maxloop)

loop_cls(fdf, 0, 2)
