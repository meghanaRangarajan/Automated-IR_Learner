def clean(s):
    print("cleaning")
    m = list()
    i=0
    while i<len(s):
        if s[i] == (0,0) or s[i] == (0,1) or s[i] == (0,2) or s[i] == (0,3) or s[i] == (0,4) or s[i] == (0,5) or s[i] == (0,4) or s[i] == (0,6) or s[i] == (0,8) or s[i] == (0,7) or s[i] == (0,9):
            if i == (len(s)-1):
                break
            x = m.pop()
            a = x[1]+s[i+1][1]+s[i][1]            
            m.append((1,a))
            i+=2
        else:
            m.append(s[i])
            i+=1
    print(m)
    return m
