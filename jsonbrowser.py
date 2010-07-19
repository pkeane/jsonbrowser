try:
    import json
except:
    import simplejson as json
from types import *
import sys
import urllib2

from Tkinter import *

jsondata = """
{
"doc":"This is a sample starter document for json-based browsing.  It includes nodes of its own (see 'todo lists') and also links to json on the web.",
"open library doc":"http://openlibrary.org/works/OL15168504W.json",
"dase collections":"http://dasebeta.laits.utexas.edu/collections.json",
"picasa web jsonc":"http://picasaweb.google.com/data/feed/api/user/pjkeane/albumid/5453894135857174993?alt=jsonc",
"freebase query":"http://www.freebase.com/api/service/search?query=perl&xx=json",
"todo lists":
    { 
    "home":["buy milk","paint house","mow the lawn"],
    "work":["finish projects","add documentation to code",
    {"title":"big project","tasks":["task one","task two","task three"]}]
    }
}
"""

class HyperlinkManager:
    """
    got this code from http://effbot.org/zone/tkinter-text-hyperlink.htm
    and edited it slight to be able to pass around data
    """
    def __init__(self, text):

        self.text = text

        self.text.tag_config("hyper", foreground="blue", underline=1)

        self.text.tag_bind("hyper", "<Enter>", self._enter)
        self.text.tag_bind("hyper", "<Leave>", self._leave)
        self.text.tag_bind("hyper", "<Button-1>", self._click)

        self.reset()

    def reset(self):
        self.links = {}

    def add(self,action,node):
        # add an action to the manager.  returns tags to use in
        # associated text widget
        tag = "hyper-%d" % len(self.links)
        self.links[tag] = {}
        self.links[tag]["action"] = action
        self.links[tag]["node"] = node 
        return "hyper", tag

    def _enter(self, event):
        self.text.config(cursor="hand2")

    def _leave(self, event):
        self.text.config(cursor="")

    def _click(self, event):
        for tag in self.text.tag_names(CURRENT):
            if tag[:6] == "hyper-":
                self.links[tag]["action"](self.links[tag]["node"])
                return
class Node():
    def __init__(self,data,title='',parent=None):
        self.title = title 
        self.data = data
        self.parent = parent

class Application():
    def __init__(self,master,node):

        self.doc_cache = {}

        scrollbar = Scrollbar(master)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.text = Text(master,wrap=WORD,yscrollcommand=scrollbar.set)
        self.text.config(padx=24,pady=24)
        self.text.pack()
        scrollbar.config(command=self.text.yview)

        self.hyperlink = HyperlinkManager(self.text)
        self.click(node)
    
    def create_breadcrumbs(self,node,set):
        set.append(node)
        if node.parent:
            return self.create_breadcrumbs(node.parent,set)
        else:
            set.reverse()
            last = set.pop()
            for n in set:
                self.text.insert(INSERT, n.title, self.hyperlink.add(self.click,n))
                self.text.insert(INSERT, " : ")
            self.text.insert(INSERT, last.title)
            self.text.insert(INSERT, "\n\n")

    def url2node(self,url,pnode):
        if self.doc_cache.has_key(url):
            return Node(json.loads(self.doc_cache[url]),url,pnode)
        if 'json' == url[-4:] or 'jsonc' == url[-5:]:
            try:
                fn = urllib2.urlopen(url)
                msg = fn.info()
                if ('application/json' == msg.gettype() or 'text/plain' ==
                    msg.gettype()):
                    jd = fn.read()
                else:
                    jd = '{"msg":"not json"}'
            except:
                print sys.exc_info()[0] 
                print url
                jd = '{"msg":"not json"}'
        else:
            jd = '{"msg":"not json"}'
        #cache document
        self.doc_cache[url] = jd
        return Node(json.loads(jd),url,pnode)

    def click(self,node):
        self.text.delete(1.0,END)
        parent = node.parent 
        #if parent:
        #    self.text.insert(INSERT, "back", self.hyperlink.add(self.click,parent))
        #    self.text.insert(INSERT, "\n\n")

        self.create_breadcrumbs(node,[])

        if type(node.data) is DictType:
            for n in node.data:
                if type(node.data[n]) is StringType or type(node.data[n]) is UnicodeType: 
                    if node.data[n][:7] == 'http://': 
                        if parent: 
                            pnode = Node(node.data,node.title,parent)
                        else:
                            pnode = Node(node.data,node.title)
                        cnode = self.url2node(node.data[n],pnode)
                        self.text.insert(INSERT,n, self.hyperlink.add(self.click,cnode))
                        self.text.insert(INSERT, "\n\n")
                    else:
                        self.text.insert(INSERT,n)     
                        self.text.insert(INSERT, " : ")
                        self.text.insert(INSERT,node.data[n])     
                        self.text.insert(INSERT, "\n\n")
                elif type(node.data[n]) is IntType:
                    self.text.insert(INSERT,n)     
                    self.text.insert(INSERT, " : ")
                    self.text.insert(INSERT,node.data[n])     
                    self.text.insert(INSERT, "\n\n")
                elif not node.data[n]:
                    self.text.insert(INSERT,n)     
                    self.text.insert(INSERT, " : ")
                    self.text.insert(INSERT,"[no value]")     
                    self.text.insert(INSERT, "\n\n")
                else:
                    if parent: 
                        pnode = Node(node.data,node.title,parent)
                        cnode = Node(node.data[n],n,pnode)
                    else:
                        pnode = Node(node.data,node.title)
                        cnode = Node(node.data[n],n,pnode)
                    self.text.insert(INSERT,n, self.hyperlink.add(self.click,cnode))
                    self.text.insert(INSERT, "\n\n")

        if type(node.data) is ListType:
            i = 0
            for n in node.data:
                if type(n) is StringType or type(n) is UnicodeType or \
                   type(n) is IntType:
                    self.text.insert(INSERT,n)     
                    self.text.insert(INSERT, "\n\n")
                else:
                    i += 1
                    if parent:
                        pnode = Node(node.data,node.title,parent)
                        cnode = Node(n,"item "+str(i),pnode)
                    else:
                        pnode = Node(node.data,node.title)
                        cnode = Node(n,"item "+str(i),pnode)
                    if type(n) is DictType:
                        if n.has_key('title'):
                            cnode = Node(n,n['title'],pnode)
                            self.text.insert(INSERT,n['title'], self.hyperlink.add(self.click,cnode))
                        elif n.has_key('id'):
                            cnode = Node(n,n['id'],pnode)
                            self.text.insert(INSERT,n['id'], self.hyperlink.add(self.click,cnode))
                        else:
                            self.text.insert(INSERT,"item "+str(i), self.hyperlink.add(self.click,cnode))
                    else:
                        self.text.insert(INSERT,"item "+str(i), self.hyperlink.add(self.click,cnode))
                    self.text.insert(INSERT, "\n\n")

        if type(node.data) is UnicodeType:
            self.text.insert(INSERT,node.data)     
            self.text.insert(INSERT, "\n\n")

        if type(node.data) is StringType:
            self.text.insert(INSERT,node.data)     
            self.text.insert(INSERT, "\n\n")

        if type(node.data) is IntType:
            self.text.insert(INSERT,node.data)     
            self.text.insert(INSERT, "\n\n")

        if type(node.data) is FloatType:
            self.text.insert(INSERT,node.data)     
            self.text.insert(INSERT, "\n\n")

if __name__ == "__main__":
    root = Tk()
    root.title("jsonbrowse")
    root.geometry("%dx%d%+d%+d" % (600, 400, 40, 40))
    if len(sys.argv) > 1:
        try:
            fn = open(sys.argv[1])
            jsondata = fn.read()
        except:
            pass
    node = Node(json.loads(jsondata),"HOME")
    app = Application(root,node)
    root.mainloop() 

