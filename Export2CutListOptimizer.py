import adsk.core
import adsk.fusion
import csv
import os
from collections import defaultdict

# This script list visible bodies, get their outbox dimensions,
# sort the x,y,z values in order to defin thickness, length and width,
# then export the table to https://www.cutlistoptimizer.com/ .csv file.
# WARNING : It doesn't mesure the real thickness and the orientation of grain.

# API manual https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-C1545D80-D804-4CF3-886D-9B5C54B2D7A2
# Based on Adam Horvath's script, modified by David Marmilloud

def get_all_components(root_comp):
    all_components = []

    def explore_component(component):
        # Ajouter le composant actuel à la liste
        all_components.append(component)

        # Explorer les occurrences du composant
        for i in range(component.occurrences.count):
            occurrence = component.occurrences[i]
            sub_component = occurrence.component
            explore_component(sub_component)

    # Démarrer l'exploration à partir du composant racine
    explore_component(root_comp)

    return all_components
    
def export_to_csv(data, filename):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Length', 'Width', 'Qty', 'Enabled', 'Component','Body'])  # En-tête
        for row in data:
            writer.writerow(row)

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface

    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    units = design.unitsManager.defaultLengthUnits
    # Get the root component of the active design.
    rootComp = design.rootComponent

    # Get occurences from root
    components = get_all_components(rootComp)
    total_lengths = defaultdict(float)
    total_counts = defaultdict(int)
    
    #Ecrit la première ligne la table html qui sera affichée à l'écran
    dialog_str = ''
    dialog_str += '<table>'
    dialog_str += '<tr>'
    dialog_str += '<th style="text-align:left;">Composant</th>'
    dialog_str += '<th style="text-align:left;">Corps</th>'
    dialog_str += '<th style="text-align:left;">Epaisseur</th>'
    dialog_str += '<th style="text-align:left;">Longueur</th>'
    dialog_str += '<th style="text-align:left;">Largeur</th>'
    dialog_str += '</tr>'

    not_visible_count = 0
    data = []   

    for subcomp in components:
        for bidx in range(0, subcomp.bRepBodies.count):
            body = subcomp.bRepBodies.item(bidx)

            if not body.isVisible:
                not_visible_count += 1
                continue

            dimvector = body.boundingBox.minPoint.vectorTo(
                body.boundingBox.maxPoint).asPoint()
            dims = sorted(dimvector.asArray())

            thickness = round(float(product.unitsManager.formatInternalValue(
                dims[0], units, False)),2)
            width = round(float(product.unitsManager.formatInternalValue(
                dims[1], units, False)),2)
            length = round(float(product.unitsManager.formatInternalValue(
                dims[2], units, False)),2)
            CompName = subcomp.name
            BodyName = body.name
                
            #ajoute une ligne au tableau qui sera exporté en csv
            data.append([length, width, 1, 'true',CompName,BodyName])    
            
            #Ecrit une ligne du message affiché à l'écran
            dialog_str += '<tr>'
            dialog_str += f'<td style="text-align:left;padding-right:15px">{CompName}</td>'
            dialog_str += f'<td style="text-align:left;padding-right:15px">{BodyName}</td>'
            dialog_str += f'<td style="text-align:left;padding-right:15px">{thickness}</td>'
            dialog_str += f'<td style="text-align:left;padding-right:15px">{length}</td>'
            dialog_str += f'<td style="text-align:left;padding-right:15px">{width}</td>'
            dialog_str += '</tr>'
    dialog_str += '</table>'
    
    # Exporte les données en CSV
    csv_filename = 'C:/Temp/export_fusion360.csv'
    try:
        export_to_csv(data, csv_filename)
        os.startfile(csv_filename)
    except Exception as e:
        ui.messageBox(f"Erreur lors de l'export CSV : {e}", "Erreur", adsk.core.MessageBoxButtonTypes.OKButtonType, adsk.core.MessageBoxIconTypes.CriticalIconType)                                                               
    #Affiche le tableau des valeurs à l'écran
    ui.messageBox(dialog_str, 'Total materials used', adsk.core.MessageBoxButtonTypes.OKButtonType,
                  adsk.core.MessageBoxIconTypes.InformationIconType)
    print(dialog_str)

