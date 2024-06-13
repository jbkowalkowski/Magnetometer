
import math as m

def mag(x,y,z): return m.sqrt(x**2+y**2+z**2)

def to_deg(r): return r*(180/m.pi)

def to_rad(d): return d/(180/m.pi)

def to_s(x,y,z):
    r=mag(x,y,z)
    th=m.atan2(y,x)
    phi=m.acos(z/r)
    return (r,to_deg(th),to_deg(phi))

def to_c(r, th, phi):
    th=to_rad(th)
    phi=to_rad(phi)
    print(f'{r} {th} {phi}')
    z=r*m.cos(phi)
    y=r*m.sin(th)*m.sin(phi)
    x=r*m.cos(th)*m.sin(phi)
    return (x,y,z)

# x y z r az roll
# -0.1302	0.2501	0.2213	0.3584	228.486	242.492

xyz=(-0.1302, 0.2501, 0.2213)
rtp=(.3584, 228.486, 242.492)

print( to_c(*rtp)) 
print( to_s(*xyz))
