# Laboratoire   : 4 - SCANNER D'UN GENOU
# Élèves        : Crüll Loris, Jaquet David, Lagier Elodie
# Date          : 31 mai 2020

import vtk
from os import path

SKIN_COLOR = (0.81, 0.63, 0.6)

BG_BOTTOM_LEFT_COLOR = (0.82, 0.82, 1)
BOTTOM_LEFT = (0, 0, 0.5, 0.5)

BG_BOTTOM_RIGHT_COLOR = (0.82, 0.82, 0.82)
BOTTOM_RIGHT = (0.5, 0, 1, 0.5)

BG_TOP_LEFT_COLOR = (1, 0.83, 0.83)
TOP_LEFT = (0, 0.5, 0.5, 1)

BG_TOP_RIGHT_COLOR = (0.82, 1, 0.83)
TOP_RIGHT = (0.5, 0.5, 1, 1)

WINDOW_SIZE = (800, 800)

FILE_NAME = 'colored_knee.vtk'


def create_structure(value, reader):
    """
    Permet de créer différentes structures selon la valeur renseignée.
    Dans notre cas : de la peau, des os, ...
    :param value:   les valeurs données au filtre.
    :param reader:  permet le lien vers l'objet filtré.

    :return:        l'objet sous plusieurs formes (filter, normals, mapper)
    """
    object_filter = vtk.vtkContourFilter()
    object_filter.SetInputConnection(reader.GetOutputPort())
    object_filter.SetValue(0, value)

    object_normals = vtk.vtkPolyDataNormals()
    object_normals.SetInputConnection(object_filter.GetOutputPort())
    object_normals.SetFeatureAngle(60)

    object_mapper = vtk.vtkPolyDataMapper()
    object_mapper.SetInputConnection(object_normals.GetOutputPort())
    object_mapper.ScalarVisibilityOff()

    return object_filter, object_normals, object_mapper


def opened_view(position, radius, resolution, color, opacity):
    """
    Permet de représenter un genou selon différentes valeurs renseignées.
    :param position:    la position du genou sur la fenêtre
    :param radius:      le rayon de la 'fenêtre' d'ouverture pour voir l'os du genou
    :param resolution:  la résolution
    :param color:       la couleur du genou
    :param opacity:     l'opacité de la peau

    :return:            l'objet sous plusieurs formes (sphere, source, mapper, actor)
    """
    object_to_build = vtk.vtkSphere()
    object_to_build.SetCenter(position)
    object_to_build.SetRadius(radius)

    object_source = vtk.vtkSphereSource()
    object_source.SetCenter(position)
    object_source.SetRadius(radius)
    object_source.SetPhiResolution(resolution)
    object_source.SetThetaResolution(resolution)
    object_source.Update()

    object_mapper = vtk.vtkPolyDataMapper()
    object_mapper.SetInputConnection(object_source.GetOutputPort())
    object_actor = vtk.vtkActor()
    object_actor.SetMapper(object_mapper)
    object_actor.GetProperty().SetColor(color)
    object_actor.GetProperty().SetOpacity(opacity)

    return object_to_build, object_source, object_mapper, object_actor


def bone_actor(mapper):
    """
    Permet de créer la structure de l'os
    :param mapper:  le mapper

    :return:        l'os sous forme d'Actor
    """
    bone = vtk.vtkActor()
    bone.SetMapper(mapper)

    return bone


def get_outline_actor(reader):
    """
    Permet de représenter un polygone entourant notre vue
    :param reader:  le reader du genou

    :return:        le polygone entourant notre vue.
    """

    outline = vtk.vtkOutlineFilter()
    outline.SetInputConnection(reader.GetOutputPort())
    outline_mapper = vtk.vtkPolyDataMapper()
    outline_mapper.SetInputConnection(outline.GetOutputPort())

    outline_actor = vtk.vtkActor()
    outline_actor.SetMapper(outline_mapper)
    outline_actor.GetProperty().SetColor(0, 0, 0)

    return outline_actor


def get_cutter_mapper(skin_mapper):
    """
    Permet de couper une certaine portion d'un objet (ici : la peau de la jambe)
    :param skin_mapper: la peau

    :return:            le mappeur a peau coupée
    """
    plane = vtk.vtkPlane()
    cutter = vtk.vtkCutter()
    cutter.SetCutFunction(plane)
    cutter.SetInputData(skin_mapper.GetInput())
    cutter.GenerateValues(19, 0, 190)  # Nb swirls vue 1

    cutter_mapper = vtk.vtkPolyDataMapper()
    cutter_mapper.SetInputConnection(cutter.GetOutputPort())
    cutter_mapper.ScalarVisibilityOff()

    return cutter_mapper


def create_renderer(actors, background, viewport, camera):
    """
    Permet de créer une représentation d'un genou pour pouvoir l'afficher sur une fenêtre
    :param actors:      les différents acteurs
    :param background:  le fond de la vue
    :param viewport:    le port de la vue
    :param camera:      la camera

    :return:            la représentation
    """
    renderer = vtk.vtkRenderer()

    for actor in actors:
        renderer.AddActor(actor)

    renderer.SetBackground(background)
    renderer.SetViewport(viewport)
    renderer.SetActiveCamera(camera)
    renderer.ResetCamera()

    return renderer


def cut_skin_actor(normals, sphere):
    """
    Permet de couper la peau de la jambre selon une sphère et des données
    :param normals:     les valeurs du clipper
    :param sphere:      le rayon de la 'fenêtre' d'ouverture pour voir l'os du genou

    :return:            la vue du genou avec la coupe
    """
    clipper = vtk.vtkClipPolyData()
    clipper.SetInputConnection(normals.GetOutputPort())
    clipper.SetClipFunction(sphere)
    clipper.GenerateClipScalarsOn()
    clipper.GenerateClippedOutputOn()
    clipper.SetValue(5)

    clipper_mapper = vtk.vtkPolyDataMapper()
    clipper_mapper.SetInputConnection(clipper.GetOutputPort())
    clipper_mapper.ScalarVisibilityOff()

    interior = vtk.vtkProperty()
    interior.SetColor(SKIN_COLOR)

    cut_view_actor = vtk.vtkActor()
    cut_view_actor.SetMapper(clipper_mapper)
    cut_view_actor.GetProperty().SetColor(SKIN_COLOR)
    cut_view_actor.SetBackfaceProperty(interior)

    return cut_view_actor


def get_distance_actor(bones, skin_mapper):
    """
    Récupère l'acteur des os du genou colorés par la distance avec la peau
    :param bones:       acteur des os
    :param skin_mapper: mapper de la peau

    :return:            acteur du genou coloré
    """
    distance_filter = get_distance_filter(bones, skin_mapper)

    distance_mapper = vtk.vtkPolyDataMapper()
    distance_mapper.SetInputData(distance_filter)
    distance_mapper.SetScalarRange(distance_filter.GetPointData().GetScalars().GetRange())

    distance_actor = vtk.vtkActor()
    distance_actor.SetMapper(distance_mapper)

    return distance_actor


def get_distance_filter(bones, mapper):
    """
    Récupère les informations de la distance entre les os et la peau.
    Comme il s'agit d'une longue opération, on vérifie si un fichier 'colored_knee.vtk' existe.
    Si ce n'est pas le cas, le fichier est créé avec les informations récupérées.
    :param bones:   acteur des os du genou
    :param mapper:  mapper de la peau de la jambe

    :return:        Le filtre de distance entre les os et la peau
    """
    if path.exists(FILE_NAME):
        polydata = read_file()
    else:
        distance_filter = vtk.vtkDistancePolyDataFilter()
        distance_filter.SetInputData(0, bones.GetMapper().GetInput())
        distance_filter.SetInputData(1, mapper.GetInput())
        distance_filter.SignedDistanceOff()
        distance_filter.Update()

        polydata = distance_filter.GetOutput()
        create_file(polydata)

    return polydata


def create_file(data):
    """
    Permet de créer un fichier où l'on écrit les données afin de réduire le temps des prochaines
    compilations.
    :param data:    les données à écrire
    """
    writer = vtk.vtkPolyDataWriter()
    writer.SetInputData(data)
    writer.SetFileName(FILE_NAME)
    writer.Write()


def read_file():
    """
    Permet de lire les données d'un fichier externe

    :return: Le fichier lu
    """
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(FILE_NAME)
    reader.Update()

    return reader.GetOutput()


def main():
    reader = vtk.vtkSLCReader()
    reader.SetFileName("vw_knee.slc")

    (skin_filter, skin_normals, skin_mapper) = create_structure(50, reader)
    (bone_filter, bone_normals, bone_mapper) = create_structure(75, reader)

    (sphere, sphere_source, sphere_mapper, sphere_actor) = opened_view((70, 40, 100), 50, 20, (0.3, 0.3, 0), 0.1)

    camera = vtk.vtkCamera()
    camera.SetViewUp(0, 0, 1)
    camera.SetPosition(0, 1, 0)

    camera.Roll(180)
    camera.Azimuth(180)

    bones = bone_actor(bone_mapper)
    outline_actor = get_outline_actor(reader)

    rings_leg_actor = vtk.vtkActor()
    rings_leg_actor.GetProperty().SetLineWidth(2)  # Epaisseur swirls
    rings_leg_actor.SetMapper(get_cutter_mapper(skin_mapper))
    rings_leg_actor.GetProperty().SetColor(SKIN_COLOR)

    actors = [bones, outline_actor, rings_leg_actor]
    renderers = [create_renderer(actors, BG_TOP_LEFT_COLOR, TOP_LEFT, camera)]

    top_right_back_skin = cut_skin_actor(skin_normals, sphere)
    top_right_back_skin.GetProperty().FrontfaceCullingOn()

    top_right_front_skin = cut_skin_actor(skin_normals, sphere)
    top_right_front_skin.GetProperty().SetOpacity(0.5)  # Transparent
    top_right_front_skin.GetProperty().BackfaceCullingOn()

    actors = [top_right_back_skin, top_right_front_skin, bones, outline_actor]
    renderers.append(create_renderer(actors, BG_TOP_RIGHT_COLOR, TOP_RIGHT, camera))

    actors = [cut_skin_actor(skin_normals, sphere), bones, outline_actor, sphere_actor]
    renderers.append(create_renderer(actors, BG_BOTTOM_LEFT_COLOR, BOTTOM_LEFT, camera))

    # Get the colored knee
    distance_actor = get_distance_actor(bones, skin_mapper)

    actors = [distance_actor, outline_actor]
    renderers.append(create_renderer(actors, BG_BOTTOM_RIGHT_COLOR, BOTTOM_RIGHT, camera))

    renderer_window = vtk.vtkRenderWindow()
    renderer_window.SetSize(WINDOW_SIZE)

    for renderer in renderers:
        renderer_window.AddRenderer(renderer)

    for i in range(0, 360):
        camera.Azimuth(1)
        renderer_window.Render()

    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renderer_window)
    style = vtk.vtkInteractorStyleTrackballCamera()
    iren.SetInteractorStyle(style)
    iren.Initialize()
    iren.Start()


if __name__ == "__main__":
    main()
