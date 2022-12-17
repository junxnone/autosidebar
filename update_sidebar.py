import os
import glob
import pandas as pd
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('--path', default='none')
args = ap.parse_args()
doc_ptn = args.path + '/*.md'

file_list = glob.glob(doc_ptn)
#file_list = glob.glob("docs/*.md")
#print(file_list)
#file_list.remove("docs/_sidebar.md")
#file_list.remove("docs/NAV.md")
#file_list.remove("docs/README.md")

#print(file_list)

fd = {"filepath": pd.Series(file_list)}
fdf = pd.DataFrame(fd)
fdf.filepath.str.split("/", expand=True)
fdf["filename"] = fdf.filepath.str.split("/", expand=True)[1]
namex = fdf.filename.str.split(".", expand=True)[0].rename("name0")
fdf = fdf.join(namex)
cls_df = fdf.filename.str.split(".", expand=True)[0].str.split("_", expand=True)
fdf = fdf.join(cls_df)
fdf.fillna(value="None", inplace=True)



fdf.to_csv("df.csv")
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
        print(cls0n)
        cls0_df = ldf[ldf[nloop] == cls0n]
        for ll in cls0_df[cls0_df[nloop+1] == 'None'].link:
            print((' ' * nloop * 2) + (f'- {ll}'))
        if nloop < maxloop:
            loop_cls(cls0_df, nloop+1, maxloop)

loop_cls(fdf, 0, 2)
