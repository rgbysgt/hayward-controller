key = [0,1]
checksum = [0,23]

a = [10,2,0,3,key[0],key[1],key[0],key[1],checksum[0],checksum[1],10,3]

x = bytearray(a)
print("someone's conversion sucks...")
print(x)

v = bytearray(len(a))
for i in range(len(a)):
    v[i] = int(a[i]).to_bytes(2, byteorder='little')[0]


print(v)
