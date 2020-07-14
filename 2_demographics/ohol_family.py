def plot_family(fam, n, t, gen):
    plot_file = 'plots/families/families_name-%s_time-%i.png' % (n, t)

    w = max(5, np.ceil(gen/5))*2.5
    h = w/1.3
    fig = plt.figure(figsize=(w,h))
    nx.nx_agraph.write_dot(fam,'tmp_family.dot')
    pos=graphviz_layout(fam, prog='dot')
    nx.draw(fam, pos, with_labels=False)
    
    plt.savefig(plot_file)
    plt.close()