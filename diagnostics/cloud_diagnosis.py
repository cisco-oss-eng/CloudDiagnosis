import click
from clint.textui import puts, colored, indent, progress
from diagnostics.keystone_diagnosis import KeystoneDiagnostics


def diagnose(lab, component):

    component_diagnostics = []

    if component == 'all':
        component_diagnostics.append(KeystoneDiagnostics(lab))
    elif component == 'keystone':
        component_diagnostics.append(KeystoneDiagnostics(lab))

    with progress.Bar(expected_size=len(component_diagnostics) * 2) as bar:
        for diagnostics in component_diagnostics:
            bar.show(1)
            diagnostics.execute()
            bar.show(1)

    for diagnostics in component_diagnostics:
        for d in diagnostics.diagnosis():
            if d[1][0] == "OK":
                puts(colored.white(d[0], bold=True) +
                     ' -- %s %s' % (d[1][1], colored.green('OK')))
            elif d[1][0] == "FAILED":
                puts(colored.white(d[0], bold=True) +
                     ' -- %s %s' % (d[1][1], colored.red('FAIL')))


@click.command()
@click.option("--labfile", help="Location to lab configuration file")
@click.option("--component", default="all",
              help="Diagnostics type (all, keystone)")
@click.option("--log_dir", default="/tmp", help="Path to log directory")
def start(labfile, component, log_dir):
    diagnose(eval(open(labfile, 'r').read()), component)


if __name__ == '__main__':
    start()
