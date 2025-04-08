# Python Script, API Version = V232
from ansys_optical_automation.speos_process.speos_simulations import Simulation


def find_sims(selection):
    """
    Parameters
    ----------
    selection
        SpaceClaim Selection

    Returns
    -------
    list
        list contain two item list first item simulation object second item derives the simulation type
    """
    sim_list = []
    if str(type(selection)) == "<type 'List[str]'>":
        for name in selection:
            if SpeosSim.SimulationDirect.Find(name):
                sim_list.append([name, "direct"])
            elif SpeosSim.SimulationInverse.Find(name):
                sim_list.append([name, "inverse"])
        return sim_list
    for item in selection.Items:
        name = item.GetName()
        if SpeosSim.SimulationDirect.Find(name):
            sim_list.append([name, "direct"])
        elif SpeosSim.SimulationInverse.Find(name):
            sim_list.append([name, "inverse"])
    return sim_list


def main():
    """Main Script function asking for input an exporting all simulation of the input selection"""
    mode = None
    try:
        argsDict
        mode = 1
    except Exception:
        mode = 0

    if mode == 0:
        input_return = InputHelper.PauseAndGetInput("Select Simulations to export.")
        if not input_return.Success:
            MessageBox.Show("to export the simulation please select a Simulation")
        sim_selection = input_return.PrimarySelection
        if len(find_sims(sim_selection)) == 0:
            MessageBox.Show("Select at least one valid simulation")
        for sim in find_sims(sim_selection):
            current_sim = Simulation(sim[0], SpeosSim, SpaceClaim, sim[1])
            current_sim.linked_export_simulation()
    else:
        sim_selection = argsDict["speos_elements"]
        if len(find_sims(sim_selection)) == 0:
            MessageBox.Show("Select at least one valid simulation")
        if len(find_sims(sim_selection)) == 0:
            MessageBox.Show("Select at least one valid simulation")
        for sim in find_sims(sim_selection):
            current_sim = Simulation(sim[0], SpeosSim, SpaceClaim, sim[1])
            current_sim.linked_export_simulation()


main()
