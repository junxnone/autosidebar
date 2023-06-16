import os
import glob
import pandas as pd
import argparse
import fileinput
import pytz
import datetime
import json

ap = argparse.ArgumentParser()
ap.add_argument('-p', '--path', default='none')
ap.add_argument('-r', '--repo_name', default='Root')

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
    xpath = files_df.basename.str.replace("^[0-9][0-9][0-9][0-9]_", '', regex=True).str.replace('_','/').rename("xpath")
    files_df = files_df.join(xpath)



    sname = files_df.basename.str.rsplit('_', expand=True, n=1)
    sname['lastname'] = sname.apply(lambda x: build_subname(x[0], x[1]), axis = 1)
    files_df['lastname'] = sname['lastname']
    files_df['title'] = files_df.apply(lambda x: get_title(x['filepath'], x['lastname']), axis = 1)
    files_df['create_date'] = files_df.apply(lambda x: get_create_date(x['filepath']), axis = 1)
    cls_df = files_df.filename.str.replace("^[0-9][0-9][0-9][0-9]_", '', regex=True).str.replace('.', '_', regex=False).str.split("_", expand=True, regex=False)
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
        patha = [0,1,2,3,4,5,6,7,8,9]
        for line in flines:
            temp = line.strip('\n')
            if line.strip('\n').strip(' ') == '':
                break
            ltitle = temp.replace(' ', '').replace('-', '').strip(' ')
            spc = temp.rstrip(' ').count('  ')
            patha[spc] = ltitle

            listpath.append('/'.join(patha[0:spc+1]))
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
write_list2txt(hist_list, os.path.join(args.path,'hist.md'))
print('- [Wiki History](/hist)')

print('\n---')
tz = pytz.timezone('Asia/Shanghai')

uddate = datetime.datetime.now(tz).strftime("%m%d")
udtime = datetime.datetime.now(tz).strftime("%H%M%S")

print('<kbd>' + '<sub>@' + udtime + uddate + '</sub></kbd>')

def dump_kg_json(df, reponame):
    kg = {"nodes":[],"links":[]}
    url='https://junxnone.github.io/' + reponame.split('/')[1] + '/#/'
    rootnode = {"id": reponame.split('/')[1],"group":0,"url":url}
    kg["nodes"].append(rootnode)
    nodelist = {}
    nodelist["0"] = []
    nodelist["0"].append(rootnode["id"])

    for i in range(1,10):
        nodelist[str(i)]=[]
        if i in df.columns:
            subdf = df[df[i]=='md']
            for index,row in subdf.iterrows():
                st = ' '
                nodeid = st.join(row['basename'].split('_')[1:])
                nodelist[str(i)].append(nodeid)
                nodeurl = url+row['link'].split('/')[1].split(')')[0]
                node = {"id": nodeid,"group":i,"url":nodeurl}
                kg["nodes"].append(node)
            if(i-1 == 0):
                node = {"id": nodeid,"group":i,"url":nodeurl}
                for tnode in nodelist[str(i)]:
                    link = {"source": nodelist["0"][0], "target": tnode, "value": i}
                    kg["links"].append(link)
            else:
                if(str(i-1) in nodelist):
                    for snode in nodelist[str(i-1)]:
                        for tnode in nodelist[str(i)]:
                            if snode in tnode:
                                link = {"source": snode, "target": tnode, "value": i}
                                kg["links"].append(link)

    with open(os.path.join(args.path,'kg.json'), 'w') as f:
        json.dump(kg, f)

dump_kg_json(fdf, args.repo_name)
