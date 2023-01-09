'''
question:
205. Isomorphic Strings
Given two strings s and t, determine if they are isomorphic.

Two strings s and t are isomorphic if the characters in s can be replaced to get t.

All occurrences of a character must be replaced with another character while
preserving the order of characters. No two characters may map to the same
character, but a character may map to itself.
'''

s=input('Enter a word: ')
t=input('Enter another word: ')
sdict={}
tdict={}
xlist=[]
ylist=[]
xres=[]
yres=[]
if(len(s)==len(t)):
    for i in range(0,len(s)):
        if((s[i]) in xlist) :
           sdict[s[i]].append(i)
           xres.append(sdict[s[i]])
        else:
            sdict[s[i]]=[i]
            xlist.append(s[i])
            xres.append(sdict[s[i]])
            
        if (t[i] in ylist):
            tdict[t[i]].append(i)
            yres.append(tdict[t[i]])
        else:
            
            tdict[t[i]]=[i]
            
            ylist.append(t[i])
            yres.append(tdict[t[i]])

    print('x ',xres)
    print('y ',yres)

    if(xres==yres):
        print('isometric')
    else:
        print('not isometric')
        
else:
    print('not isometric')


