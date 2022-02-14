import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
# Pie chart, where the slices will be ordered and plotted counter-clockwise:
labels = ["standalone", "datacoord", "datanode", "indexcoord", "indexnode", "proxy", "pulsar", "querycoord", "querynode", "rootcoord", "etcd", "minio"]
failure_cnt = [0, 1, 1, 1, 1, 1, 9, 1, 2, 2, 1, 1]
# explode = (0, 0.1, 0, 0)  # only "explode" the 2nd slice (i.e. 'Hogs')

fig1, ax1 = plt.subplots()
patches, texts, autotexts = ax1.pie(failure_cnt, labels=labels, autopct='%1.1f%%',
        shadow=False, startangle=90)
ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
# proptease = fm.FontProperties()
# proptease.set_size('xx-small')
# # font size include: ‘xx-small’,x-small’,'small’,'medium’,‘large’,‘x-large’,‘xx-large’ or number, e.g. '12'
# plt.setp(autotexts, fontproperties=proptease)
# plt.setp(texts, fontproperties=proptease)

# plt.savefig('Demo_official.jpg')
plt.show()