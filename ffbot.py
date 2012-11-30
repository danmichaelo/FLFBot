#encoding=utf-8
from __future__ import unicode_literals

import time
from datetime import datetime, timedelta
import sqlite3
import mwclient
import urllib
from danmicholoparser import DanmicholoParser, DanmicholoParseError
from wp_private import botlogin

import locale
locale.setlocale(locale.LC_TIME, 'no_NO.utf-8'.encode('utf-8'))

no = mwclient.Site('no.wikipedia.org')
no.login(*botlogin)

def find_rev(p, templates):
    #logger.info("    %s: " % (p)
    foundCleanRev = False
    revschecked = 0
    rev_id = -1
    rev_parent = -1
    while foundCleanRev == False:
        if rev_parent == 0:
            #logger.info('    %s: tagged from beginning (%s)' % (p,q))
            break
        elif rev_parent == -1:
            query = no.api('query', prop='revisions', rvprop='ids|timestamp|user|content|comment', rvdir='older', titles=p, rvlimit=10)['query']
        else:
            query = no.api('query', prop='revisions', rvprop='ids|timestamp|user|content|comment', rvdir='older', titles=p, rvlimit=10, rvstartid=rev_parent)['query']
        #print 'api call',rev_parent
        pid = query['pages'].keys()[0]
        if pid == '-1':
            #logger.info("(slettet, pid=-1)")
            break
        else:
            if 'revisions' in query['pages'][pid].keys():
                revs = query['pages'][pid]['revisions']
                for rev in revs:
                    revschecked += 1
                    #logger.debug(" checking (%s)"%rev['revid'])
                    if '*' in rev.keys() and 'user' in rev.keys():   # revision text and/or user may be hidden
                        txt = rev['*']
                        if txt.find(u'#OMDIRIGERING [[') != -1 or txt.find(u'#REDIRECT[[') != -1:
                            #logger.info('    %s: found redirect page' % (p))
                            #logger.info("   (omdirigeringsside) ")
                            foundCleanRev = True
                            rev_id = -1
                            break
                        foundCleanRev = True
                        for t in templates:
                            if txt.lower().find(u'{{%s'%t) != -1:
                                foundCleanRev = False
                        if foundCleanRev:
                            break
                        else:
                            rev_id = rev['revid']
                            rev_user = rev['user']
                            rev_comment = rev['comment']
                            rev_parent = rev['parentid']
                            rev_ts = rev['timestamp']
                    else:
                        rev_parent = rev['parentid']
    if rev_id == -1:
        #logger.warning('    %s: didn\'t find template for %s' % (p,q))
        #logger.info("Fant ikke merking!")
        return False
    else:
        rev_ts = datetime.strptime(rev_ts,'%Y-%m-%dT%H:%M:%SZ')
        return { 'id': rev_id, 'parent': rev_parent, 'date': rev_ts, 'user': rev_user, 'comment': rev_comment }
        
        #logger.info('    %s: found rev %s by %s (checked %d revisions)' % (p,lastrev,lastrevuser))
        #cur = self.sql.cursor()
        #if not self.dryrun:
        #    cur.execute(u'''INSERT INTO cleanlog (date, category, action, page, user, revision)
        #        VALUES(?,?,?,?,?,?)''', tuple([revts.strftime('%F %T'), catkey, q, p, lastrevuser, lastrev]))
        #cur.close()


pages = [c for c in no.categories['Artikler som bør flyttes']]
sql = sqlite3.connect('ffbot.db')
cur = sql.cursor()
in_db = False
entries = []
for p in pages:
    cur.execute('SELECT target, target2, date, revid, parentid, user, comment, reason FROM list WHERE page=?', [p.name])
    s = cur.fetchall()
    in_db = (len(s) > 0)
    print p.name
    if in_db:
        rev = { 'to': s[0][0], 'to2': s[0][1], 'date': datetime.strptime(s[0][2], '%Y-%m-%d'), 
                'id': s[0][3], 'parent': s[0][4], 'user': s[0][5], 'comment': s[0][6], 'reason': s[0][7] }
        
    else:
        dp = DanmicholoParser(p.edit(readonly = True))
        k = dp.templates.keys()
        if 'flytt' in k:
            t = dp.templates['flytt'][0]
        elif 'flytting' in k:
            t = dp.templates['flytting'][0]
        else:
            print "> fant ikke noen mal"
            continue
        tk = t.parameters.keys()
        if not 1 in tk:
            print " > Ingen parametre gitt til malen!"
            continue

        print ' -> %s' % t.parameters[1]
        fra = '[[%s]]' % p.name

        rev = find_rev(p.name, ['flytt','flytting'])
        if rev == False:
            continue

        rev['to'] = t.parameters[1]
        rev['to2'] = ''
        rev['reason'] = ''
        if 2 in tk:
            #print ' eller: %s' % t.parameters[2]
            rev['to2'] += t.parameters[2]
        if 'begrunnelse' in tk:
            print ' begrunnelse: %s' % t.parameters['begrunnelse']
            rev['reason'] = t.parameters['begrunnelse'].strip()

        vals = [p.name, rev['to'], rev['to2'], rev['date'].strftime('%F'), rev['id'], rev['parent'], rev['user'], rev['comment'], rev['reason'] ]
        cur.execute('INSERT INTO list (page, target, target2, date, revid, parentid, user, comment, reason) VALUES (?,?,?,?,?,?,?,?,?)', vals)

    #begrunnelse = "<span style='color:#999;'>''Ikke gitt''</span>"

    q = { 'title': p.name.encode('utf-8'), 'oldid': rev['id'], 'diff': 'prev' }
    link = '[%s Foreslått]' % ('//' + no.host + no.site['script'] + '?' + urllib.urlencode(q))
    #submitter = ''<br />%s' % (rev['user'], rev['user'], link)
    
    entry = ''
    if len(rev['reason']) != 0:
        entry += '<abbr style="color: #999; " title="Begrunnelse i mal">B:</span> %s<br />' % rev['reason']
    if len(rev['comment']) != 0:
        entry += '<abbr style="color: #999; " title="Redigeringsforklaring">R:</abbr> <nowiki>%s</nowiki><br />' % rev['comment']
    entry += "<small>''%s av [[Bruker:%s|%s]] den %s''</small>" % (link, rev['user'], rev['user'], rev['date'].strftime('%e. %B %Y'))

    fra = '[[%s]]' % p.name
    til = '[[%s]]' % rev['to']
    if len(rev['to2']) != 0:
        til += '<br />&nbsp;&nbsp; eller [[%s]]' % rev['to2']

    text = '|-\n| %s<br /> → %s \n| %s \n' % (fra, til, entry)
    entries.append([rev['date'], text])

    #time.sleep(1)
            
sql.commit()

pnames = [p.name for p in pages]
for row in cur.execute('SELECT page FROM list'):
    n = row[0]
    if not n in pnames:
        print "Page %s found in db, but not in cat. Removing from db" % n
        # DELETE FROM .. WHERE page=? , n

entries.sort(key = lambda x: x[0])
text = '{| class="wikitable"\n! Forslag !! Begrunnelse \n' + ''.join([e[1] for e in entries]) + '|}\n'

page = no.pages['Bruker:DanmicholoBot/Sandkasse']
page.edit()
page.save(text, 'Oppdaterer')



