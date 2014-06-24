#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: garcia.wul
@contact: garcia.wul@alibaba-inc.com
@date: 2014/06/23
"""

import os
import sqlite3
import urllib2
import shutil
import tarfile
import hashlib
import codecs
import json

from mako.template import Template
from pyquery import PyQuery

def removeChinesePrefix(name):
    newName = name.lstrip("类:").lstrip("事件:")
    newName = newName.lstrip()
    return newName

def resultsContains(results, path):
    flag = False
    for result in results:
        if result["path"] == path:
            flag = True
    return flag

currentPath = os.path.join(os.path.dirname(os.path.realpath(__file__)))
name = "node"

baseName = "node-zh"
output = baseName + ".docset"
appName = "dash-" + baseName
tarFileName = baseName + ".tgz"
feedName = baseName + ".xml"
version = "0.10.18"

url = "http://nodeapi.ucdok.com/api/all.html"
content = urllib2.urlopen(url).read()
content = content.decode("utf-8").encode("utf-8")
jQuery = PyQuery(content)

types = {
    "event": "Event",
    "module": "Module",
    "method": "Method",
    "class": "Class",
    "var": "Variable",
}

items = jQuery("#toc li a").items()
metaData = {}
for item in items:
    text = item.text().strip()
    if type(text) is unicode:
        text = text.encode("utf-8")
    elif type(text) is str:
        text = text.decode("utf-8").encode("utf-8")
    metaData[text] = item.attr("href").encode("utf-8")

url = "http://nodeapi.ucdok.com/api/all.json"
content = urllib2.urlopen(url).read()
content = content.decode("utf-8").encode("utf-8")
content = json.loads(content, encoding="utf-8")
results = []
for g in content["globals"]:
    textRaw = g["textRaw"].encode("utf-8")
    if metaData.has_key(textRaw) and not resultsContains(results, metaData[textRaw]):
        results.append({
            "name": removeChinesePrefix(textRaw),
            "type": "Variable",
            "path": "index.html" + metaData[textRaw]
        })
    if g.has_key("methods"):
        for method in g["methods"]:
            textRaw = method["textRaw"].encode("utf-8")
            if metaData.has_key(textRaw) and not resultsContains(results, metaData[textRaw]):
                results.append({
                    "name": removeChinesePrefix(textRaw),
                    "type": "Method",
                    "path": "index.html" + metaData[textRaw]
                })
for g in content["vars"]:
    textRaw = g["textRaw"].encode("utf-8")
    if metaData.has_key(textRaw) and not resultsContains(results, metaData[textRaw]):
        results.append({
            "name": removeChinesePrefix(textRaw),
            "type": "Variable",
            "path": "index.html" + metaData[textRaw]
        })
for g in content["methods"]:
    textRaw = g["textRaw"].encode("utf-8")
    if metaData.has_key(textRaw) and not resultsContains(results, metaData[textRaw]):
        results.append({
            "name": removeChinesePrefix(textRaw),
            "type": "Method",
            "path": "index.html" + metaData[textRaw]
        })
for g in content["modules"]:
    textRaw = g["textRaw"].encode("utf-8")
    if metaData.has_key(textRaw) and not resultsContains(results, metaData[textRaw]):
        results.append({
            "name": removeChinesePrefix(textRaw),
            "type": "Module",
            "path": "index.html" + metaData[textRaw]
        })
    if g.has_key("methods"):
        for method in g["methods"]:
            textRaw = method["textRaw"].encode("utf-8")
            if metaData.has_key(textRaw) and not resultsContains(results, metaData[textRaw]):
                results.append({
                    "name": removeChinesePrefix(textRaw),
                    "type": types[method["type"]],
                    "path": "index.html" + metaData[textRaw]
                })

# Step 1: create the docset folder
docsetPath = os.path.join(currentPath, output, "Contents", "Resources", "Documents")
if not os.path.exists(docsetPath):
    os.makedirs(docsetPath)

# Step 2: Copy the HTML Documentation
fin = codecs.open(os.path.join(docsetPath, "index.html"), "w", "utf-8")
for link in jQuery("link").items():
    jQuery(link).attr("href", jQuery(link).attr("href").lstrip("/"))
newContent = jQuery.html()
fin.write(newContent)
fin.close()

# Step 2.1 下载CSS和JS
links = [
    "http://nodeapi.ucdok.com/public/api_assets/style.css",
    "http://nodeapi.ucdok.com/public/api_assets/sh.css",
    "http://nodeapi.ucdok.com/public/api_assets/sh_main.js",
    "http://nodeapi.ucdok.com/public/api_assets/sh_javascript.min.js",
    "http://nodeapi.ucdok.com/public/js/jquery.js"
]
for link in links:
    path = link.replace("http://nodeapi.ucdok.com/", "")
    fields = path.split("/")
    if len(fields) >= 2:
        dirPath = os.path.join(docsetPath, os.path.sep.join(fields[:-1]))
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        fin = open(os.path.join(docsetPath, os.path.sep.join(fields)), "w")
        fin.write(urllib2.urlopen(link).read())
        fin.close()

# Step 3: create the Info.plist file
infoTemplate = Template('''<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
<key>CFBundleIdentifier</key>
<string>${name}</string>
<key>CFBundleName</key>
<string>${name}</string>
<key>DocSetPlatformFamily</key>
<string>${name}</string>
<key>dashIndexFilePath</key>
<string>index.html</string>
<key>dashIndexFilePath</key>
<string>index.html</string>
<key>isDashDocset</key><true/>
<key>isJavaScriptEnabled</key><true/>
</dict>
</plist>''')
infoPlistFile = os.path.join(currentPath, output, "Contents", "Info.plist")
fin = open(infoPlistFile, "w")
fin.write(infoTemplate.render(name = name))
fin.close()

# Step 4: Create the SQLite Index
dbFile = os.path.join(currentPath, output, "Contents", "Resources", "docSet.dsidx")
if os.path.exists(dbFile):
    os.remove(dbFile)
db = sqlite3.connect(dbFile)
cursor = db.cursor()

try:
    cursor.execute("DROP TABLE searchIndex;")
except Exception:
    pass

cursor.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
cursor.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

insertTemplate = Template("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('${name}', '${type}', '${path}');")

# Step 5: Populate the SQLite Index
for result in results:
    try:
        sql = insertTemplate.render_unicode(name = result["name"].decode("utf-8"),
            type = result["type"].decode("utf-8"),
            path = result["path"].decode("utf-8"))
    except Exception:
        continue
    print sql
    cursor.execute(sql)
db.commit()
db.close()

# Step 6: copy icon
shutil.copyfile(os.path.join(currentPath, "icon.png"),
    os.path.join(currentPath, output, "icon.png"))
shutil.copyfile(os.path.join(currentPath, "icon@2x.png"),
    os.path.join(currentPath, output, "icon@2x.png"))

# Step 7: 打包
if not os.path.exists(os.path.join(currentPath, "dist")):
    os.makedirs(os.path.join(currentPath, "dist"))
tarFile = tarfile.open(os.path.join(currentPath, "dist", tarFileName), "w:gz")
for root, dirNames, fileNames in os.walk(output):
    for fileName in fileNames:
        fullPath = os.path.join(root, fileName)
        print fullPath
        tarFile.add(fullPath)
tarFile.close()

# Step 8: 更新feed url
feedTemplate = Template('''<entry>
    <version>${version}</version>
    <sha1>${sha1Value}</sha1>
    <url>https://raw.githubusercontent.com/magicsky/${appName}/master/dist/${tarFileName}</url>
</entry>''')
fout = open(os.path.join(currentPath, "dist", tarFileName), "rb")
sha1Value = hashlib.sha1(fout.read()).hexdigest()
fout.close()
fin = open(os.path.join(currentPath, feedName), "w")
fin.write(feedTemplate.render(sha1Value = sha1Value, appName = appName, tarFileName = tarFileName, version = version))
fin.close()
