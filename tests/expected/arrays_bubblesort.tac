func_begin main
a[0] = 5
a[1] = 2
a[2] = 4
a[3] = 1
a[4] = 3
i = 0
L1:
t1 = i < 5
if_false t1 goto L2
j = 0
L3:
t2 = 4 - i
t3 = j < t2
if_false t3 goto L4
t4 = a[j]
t5 = j + 1
t6 = a[t5]
t7 = t4 > t6
if_false t7 goto L5
t8 = a[j]
tmp = t8
t9 = j + 1
t10 = a[t9]
a[j] = t10
t11 = j + 1
a[t11] = tmp
L5:
t12 = j + 1
j = t12
goto L3
L4:
t13 = i + 1
i = t13
goto L1
L2:
k = 0
L6:
t14 = k < 5
if_false t14 goto L7
t15 = a[k]
print t15
t16 = k + 1
k = t16
goto L6
L7:
return 0
func_end main
