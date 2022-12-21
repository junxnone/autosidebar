import os
import glob
import pandas as pd
import argparse
import fileinput

ap = argparse.ArgumentParser()
ap.add_argument('--path', default='none')
args = ap.parse_args()

doc_ptn = os.path.join(args.path, '*.md')
file_list = glob.glob(doc_ptn)

def txt2list(file_path):
    wlist = []
    with open(file_path, 'r') as fn:
        flines = fn.readlines()
        for line in flines:
            temp = line.strip('\n')
            wlist.append(temp)
    return wlist

sort_fpath = os.path.join(args.path, 'sidebar.md')
sort_list = []
if sort_fpath in file_list:
    sort_list = txt2list(sort_fpath)

ignore_files = ['_sidebar.md', 'NAV.md', 'README.md', 'sidebar.md', 'hist.md']
for igf in ignore_files:
    igf_path = os.path.join(args.path, igf)
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
loop_max = fdf.columns.tolist()[-1]
fdf[fdf.columns.tolist()[-1] + 1] = "None"

def search_sort_cls(df, level):
    cls_list = df[level].value_counts().index.tolist()
    if "None" in cls_list:
        cls_list.remove("None")
    if "" in cls_list:
        cls_list.remove("")
    return cls_list


def build_subname(a,b):
    if b is None:
        return a
    else:
        return b

sname = fdf.name0.str.rsplit('_', expand=True, n=1)
sname['lastname'] = sname.apply(lambda x: build_subname(x[0], x[1]), axis = 1)
fdf['lastname'] = sname['lastname']

def get_title(filepath, lastname):
    title = 'notitle'
    for line in fileinput.input(files=filepath):
        if line.startswith('# '):
            title = line.replace('# ', '').strip('\n').strip(' ')
            break
    fileinput.close()
    if (title == 'notitle'):
        return lastname
    return title

fdf['title'] = fdf.apply(lambda x: get_title(x['filepath'], x['lastname']), axis = 1)

def get_create_date(filepath):
    date = 'nodate'
    for line in fileinput.input(files=filepath):
        if line.startswith('Created @'):
            date = line.replace('Created @ | `', '').replace('Z`', '').strip('\n').strip(' ')
            break
    fileinput.close()

    return date

fdf['create_date'] = fdf.apply(lambda x: get_create_date(x['filepath']), axis = 1)
fdf['link'] = '[' + fdf.title + '](/' + fdf.name0 + ')'

date_linkl = fdf.sort_values('create_date', ascending=False).link.tolist()
date_datel = fdf.sort_values('create_date', ascending=False).create_date.tolist()

hist_list = ['# Wiki History\n']

for ilink, idate in zip(date_linkl, date_datel):
    if idate != 'nodate':
        ds = idate.split('T')[0]
        hist_list.append(f'- {ds}   {ilink}')

def write_list2txt(wlist, file_path):
    with open(file_path, 'w') as fn:
        for line in wlist:
            fn.write(str(line) + '\n')
write_list2txt(hist_list, 'docs/hist.md')

def loop_cls(ldf, sloop, nloop, maxloop):
    list_0 = search_sort_cls(ldf, nloop)
    list_0s = []
    for ix in sort_list:
        ix = ix.replace(' ', '')
        if ix in list_0:
            list_0s.append(ix)
            list_0.remove(ix)
    list_x = list_0s + list_0
    for cls0n in list_x:
        cls0_df = ldf[ldf[nloop] == cls0n]

        if (len(cls0_df[cls0_df[nloop+1] == 'md'])):
            for ll in cls0_df[cls0_df[nloop+1] == 'md'].link:
                print((' ' * (nloop - sloop) * 2) + (f'- {ll}'))
        elif (cls0n != 'md'):
            print((' ' * nloop * 2) + f'- {cls0n}')
        if nloop < maxloop:
            loop_cls(cls0_df, sloop, nloop+1, maxloop)

loop_cls(fdf, 1, 1, 2)
print('- [Wiki History](/hist)')
