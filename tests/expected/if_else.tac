func_begin main
x = 10
t1 = x > 5
if_false t1 goto L1
print 1
goto L2
L1:
print 0
L2:
return 0
func_end main
