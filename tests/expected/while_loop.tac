func_begin main
i = 0
s = 0
L1:
t1 = i < 5
if_false t1 goto L2
t2 = s + i
s = t2
t3 = i + 1
i = t3
goto L1
L2:
print s
return 0
func_end main
