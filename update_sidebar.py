import os
import glob
import pandas as pd
import argparse
import fileinput


ap = argparse.ArgumentParser()
ap.add_argument('-p', '--path', default='none')
args = ap.parse_args()


def search_docs(docs_path):
    doc_ptn = os.path.join(docs_path, '*.md')
    files_list = glob.glob(doc_ptn)

    ignore_files = ['_sidebar.md', 'NAV.md', 'README.md', 'sidebar.md', 'hist.md']
    for igf in ignore_files:
        igf_path = os.path.join(docs_path, igf)
        if igf_path in files_list:
            files_list.remove(igf_path)
    return files_list

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

def build_subname(a,b):
    if b is None:
        return a
    else:
        return b

def get_create_date(filepath):
    date = 'nodate'
    for line in fileinput.input(files=filepath):
        if line.startswith('Created @'):
            date = line.replace('Created @ | `', '').split('T')[0]
            break
    fileinput.close()

    return date



def build_df(files_list):
    files_dict = {"filepath": pd.Series(files_list)}
    files_df = pd.DataFrame(files_dict)
    files_df["filename"] = files_df.filepath.str.split("/", expand=True)[1]

    basename = files_df.filename.str.split(".", expand=True)[0].rename("basename")
    files_df = files_df.join(basename)
    xpath = files_df.basename.str.replace("[0-9][0-9][0-9][0-9]_", '', regex=True).str.replace('_','/').rename("xpath")
    files_df = files_df.join(xpath)



    sname = files_df.basename.str.rsplit('_', expand=True, n=1)
    sname['lastname'] = sname.apply(lambda x: build_subname(x[0], x[1]), axis = 1)
    files_df['lastname'] = sname['lastname']
    files_df['title'] = files_df.apply(lambda x: get_title(x['filepath'], x['lastname']), axis = 1)
    files_df['create_date'] = files_df.apply(lambda x: get_create_date(x['filepath']), axis = 1)
    cls_df = files_df.filename.str.replace("[0-9][0-9][0-9][0-9]_", '', regex=True).str.replace('.', '_', regex=False).str.split("_", expand=True, regex=False)
    files_df = files_df.join(cls_df)
    files_df.fillna(value="None", inplace=True)
    files_df['link'] = '[' + files_df.title + '](/' + files_df.basename + ')'

    return files_df

def build_rules(file_path):
    listpath = []
    lstk = []
    lastspc = 0
    with open(file_path, 'r') as fn:
        flines = fn.readlines()
        for line in flines:
            temp = line.strip('\n')
            if line.strip('\n').strip(' ') == '':
                break
            if temp.startswith(' '):
                ltitle = temp.replace(' ', '').replace('-', '').strip(' ')
                spc = temp.count('  ')
                if lastspc < spc:
                    lstk.append(ltitle)
                elif lastspc == spc:
                    lstk.pop()
                    lstk.append(ltitle)
                else:
                    lstk=lstk[:-2]
                    lstk.append(ltitle)
                lastspc = spc
            if temp.startswith('- '):
                ltitle = temp.replace('- ', '').strip(' ')
                lstk = [ltitle]
                lastspc = 0
            listpath.append('/'.join(lstk))
    return listpath

spath = os.path.join(args.path, 'sidebar.md')

rulespath = build_rules(spath)
flist = search_docs(args.path)
fdf = build_df(flist)

def series2set(ses):
    cls_set = ses.value_counts().index.tolist()
    if "None" in cls_set:
        cls_set.remove("None")
    if "" in cls_set:
        cls_set.remove("")
    if "md" in cls_set:
        cls_set.remove("md")
    return cls_set

def buildsortseq(rulespath):
    sdf = pd.DataFrame(rulespath, columns=['path'])
    sdf = sdf.path.str.split('/', expand=True)
    sdf.fillna(value="None", inplace=True)

    return sdf

def resort_list(inlist, seqlist):
    rlist = []
    for it in seqlist:
        if it in inlist:
            rlist.append(it)
    olist = list(set(inlist) - set(rlist)) 
    return rlist + sorted(olist)

from functools import reduce


rdup = lambda x,y:x if y in x else x + [y]


def sort_df(df, index, seq_df):
    curlist = series2set(df[index])
    seqlist = []
    if index < seq_df.columns.size:
        seqlist = seq_df[index].tolist()
        seqlist = reduce(rdup, [[], ] + seqlist)
        if 'None' in seqlist:
            seqlist.remove("None")
    curlist = resort_list(curlist, seqlist)
    strhead = '  ' * index + '- '
    for it in curlist:
        sub_df = df[df[index] == it].reset_index(drop=True)
        itdf = sub_df[(sub_df[index+1] == 'md') & (sub_df[index] == it)]
        subseq_df = pd.DataFrame()
        if index < seq_df.columns.size:
            subseq_df = seq_df[seq_df[index] == it].reset_index(drop=True)
        if len(itdf) > 0:
            for il in itdf.link:
                print(strhead + il)
        else:
            print(strhead + it)
        if len(sub_df) > 0:
            sort_df(sub_df, index + 1, subseq_df)
 
seq_df = buildsortseq(rulespath)

sort_df(fdf, 0, seq_df)


datedf = fdf.sort_values('create_date', ascending=False)
datedf['flink'] = '[' + fdf.xpath.str.replace('/', ' ') + '](/' + fdf.basename + ')'

date_linkl = datedf.flink.tolist()
date_datel = datedf.create_date.tolist()

hist_list = ['# Wiki History\n']
for ilink, idate in zip(date_linkl, date_datel):
    if idate != 'nodate':
        hist_list.append(f'- {idate}' + ' '*8 +  ilink)

def write_list2txt(wlist, file_path):
    with open(file_path, 'w') as fn:
        for line in wlist:
            fn.write(str(line) + '\n')
write_list2txt(hist_list, 'docs/hist.md')
print('- [Wiki History](/hist)')
