import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random

fig, ax = plt.subplots(dpi=200)

print("\nGenerating placement image...\n")

for net, netinfo in ctx.nets:
    print(net)
    print(netinfo.users)

for cell, cellinfo in ctx.cells:
    if cellinfo.bel:
        #print("Cell %s   %s" % (cell, cellinfo.type))
        bel = cellinfo.bel
        loc = ctx.getBelLocation(bel)
        x = int(loc.x)
        y = int(loc.y)

        color = 'black'
        COLOR_TABLE = [
          ('Vex', 'gray'),
          ('Cfu', 'seagreen'),
          ('Cfu.core', 'lime'),
          ('Cfu.core.sysarray', 'red'),
          ('Cfu.core.ppp', 'violet'),
          ('Cfu.core.f0', 'yellow'),
          ('Cfu.core.f1', 'tan'),
        ]
        for match, c in COLOR_TABLE:
          if match in cell:
            color = c

        mul = "MULT" in bel
        ebr = "EBR" in bel

        # Set color for LRAMs
        lram = "SP512K" in cell
        arena = "DPSC512K" in cell
        color='tan' if arena else ('bisque' if lram else color)

        if mul:
            ax.add_patch(mpatches.Circle(
                [x, y+0.5], 0.7,
                color=color,
                ec='white',
                fill=True
                ))
        elif ebr or lram or arena:
            ax.add_patch(mpatches.Rectangle(
                [x, y-0.2], 1.6, 1.6,
                color=color,
                ec='white',
                fill=True
                ))
        else:
            rx = random.uniform(0,0.7)
            ry = random.uniform(0,0.7)
            ax.add_patch(mpatches.Rectangle(
                [x+rx, y+ry], 0.1, 0.1,
                color=color,
                fill=True
                ))

ax.set_aspect('equal')
nl = ',\n'
comma = ', '
ax.set_title(''.join([f'{match}={c}{nl if i&1 else comma}' for i, (match, c) in enumerate(COLOR_TABLE)]) +
    'Black=LiteX, Circle=DSP, Square=MEM')
ax.autoscale_view()
#plt.show()
plt.savefig("placement.png", format="png")
print("Done\n")

# Uncommenting this will cause nextpnr to stop without running routing (but still show the placement plot)
# exit()
