
#    Addon info
bl_info = {
    'name': 'Interpolation',
    'author': 'Marc Guerrero Palanca, Tatsiana Palikarpava Alberto Pérez Abad',
    'location': 'View3D > Tools > Movimiento',
    'category': 'Movement'
    }
 
import bpy
import numpy as np
import math
import random
from mathutils import Vector
    

############################################################################################################ 
def interpola_valores(frame, f_ant, f_sig, f_ant_ant, f_sig_sig, pos_ant_ant,pos_ant,pos_sig,pos_sig_sig, interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia, coord):
    """Parametros: frame actual, fotograma clave anterior, fotograma clave siguiente, fotograma clave anterior del anterior,
      fotograma clave siguiente del siguiente, metodo de interpolación, objeto, tau, amplitud maximal, boolean aleatorio, valor de frecuencia y  el eje de cordenada [x,y,z] => [0,1,2]"""
    if coord >= 0 and coord <= 2:
        kf_list = bpy.data.objects[object].animation_data.action.fcurves.find('location', index = coord)
    else:
        return
    
    u = (frame - f_ant)/(f_sig - f_ant)
    
    if interpolacion != "Lineal" and interpolacion != "Hermite" and interpolacion != "Catmull-Rom":
        print( "Error en la interpolacion, solo puede ser Lineal, Hermite o Catmull-Rom")
        return
    else:
        if interpolacion == "Lineal":
            pos = lineal(u, pos_ant[coord], pos_sig[coord])
            
        if interpolacion == "Hermite":                    
            
            actionName = bpy.data.objects[object].animation_data.action.name
            action = bpy.data.actions[actionName]
            bpy.context.scene.frame_set(f_ant)
            vel1 = bpy.data.objects[object].velocity[coord]
            bpy.context.scene.frame_set(f_sig)
            vel2 = bpy.data.objects[object].velocity[coord]
            pos = hermite(u, pos_ant[coord], pos_sig[coord], vel1, vel2)
              
        if interpolacion == "Catmull-Rom":
            pos = catmull_rom(u,pos_ant_ant[coord],pos_ant[coord],pos_sig[coord],pos_sig_sig[coord],tau)
            
        if aleatorio:
            aumento = vibrar(Amplitude_Max,frame, frecuencia)
        else:
            aumento = 0
            
        bpy.context.scene.frame_set(frame)
        
        bpy.data.objects[object].location[coord] = pos + aumento
        
        bpy.data.objects[object].keyframe_insert(data_path = "location")
    
    
###################################################################################################################    
def lineal (u, pos1, pos2):
    """Interpolación lineal utilizando la posición del fotograma clave anterior y la posición del fotograma clave siguiente
     y el coeficiente u entre 0 y 1"""
     
    pos = pos1 + u * (pos2 - pos1)
    
    return pos

    
def hermite(u, pos1, pos2, vel1, vel2):
    """ Hermite interpolation, which uses the positions in previous and next keyframes and velocities, calculated using keyframe before previos and after next"""
    pos = (1 - 3 * pow(u, 2) + 2 * pow(u, 3)) * pos1 + pow(u, 2) * (3 - 2 * u) * pos2 + u * (u - 1) * vel1 + pow(u, 2) * (u - 1) * vel2
    
    return pos

def catmull_rom(u,pos_ant_ant,pos_ant,pos_sig,pos_sig_sig,tau):
    """Catmull-Rom interpolation. It can use as a base Hermite interpolation. """
    #c0 = pos_ant
    #c1 = tau * (pos_sig - pos_ant_ant)
    #c2 = 3 * (pos_sig - pos_ant) - tau * (pos_sig_sig - pos_ant) - 2 * tau * (pos_sig - pos_ant_ant)
    #c3 = -2 * (pos_sig - pos_ant) + tau * (pos_sig_sig - pos_ant) + tau * (pos_sig - pos_ant_ant)
    #pos = c0 + c1 * u + c2 * pow(u, 2) + c3 * pow(u, 3)
    
    ## Forma profesor ##
    vel1 = (pos_sig - pos_ant_ant) * tau
    vel2 = (pos_sig_sig - pos_ant) * tau
    
    pos = hermite(u,pos_ant,pos_sig,vel1,vel2)
    
    return pos
############################################################################################################

def vibrar(Amplitude_Max, frame, frecuencia):
    """Esta función realiza que el objeto realice una vibración mientras realiza un recorrido"""
    
    # Desfase de la onda en caso de que la frecuencia no sea 0

    PHI = math.radians(random.randint(0,360));
    
    # Apmlitude de la onda en el eje
    Amplitude = random.uniform(0,Amplitude_Max);
    
    Aumento = Amplitude * math.sin( frecuencia * frame + PHI);

    return Aumento

############################################################################################################

# function to create or update empties
# returns a vector of tuples (frame,velocity determined by the orientation and scale) of each empty

def createEmptiesAndGetVelocityVector(action):
    actionName = action.name
    # check if exists a collection with the same name of the action
    collection = bpy.data.collections.get(actionName)
    if collection is None:
        # if the collection not exists then create it
        collection = bpy.data.collections.new(actionName)
        bpy.context.scene.collection.children.link(collection)        

    cx = action.fcurves.find('location',index=0).keyframe_points
    cy = action.fcurves.find('location',index=1).keyframe_points
    cz = action.fcurves.find('location',index=2).keyframe_points

    # for each keyframe check if exists an empty object in the collection
    for i in range(len(cx)):
        # get the position of the KF
        pos = Vector([cx[i].co[1], cy[i].co[1], cz[i].co[1]])
        emptyObj = collection.objects.get(str(i))

        if emptyObj is None:
            # if not exists create it
            emptyObj = bpy.data.objects.new( "empty", None )
            emptyObj.empty_display_size = 2
            emptyObj.empty_display_type = 'SINGLE_ARROW' 
            emptyObj.name = str(i)
            collection.objects.link(emptyObj)
            
            # else set the initial orientation to look at the next KFb

        if i+1 < len(cx):
            pos2 = Vector([cx[i+1].co[1], cy[i+1].co[1], cz[i+1].co[1]])
            rot = (pos2 - pos).to_track_quat('Z','Y')
            emptyObj.rotation_euler = rot.to_euler()       

        # set the location to the empty object
        emptyObj.location = Vector([cx[i].co[1], cy[i].co[1], cz[i].co[1]])       

    # force update the scene, necessary if new empties have been created

    bpy.context.view_layer.update()      

    # for each keyframe get the velocity (scaled direction of the single arrow)

    # create a vector of tuples (frame, velocity) where velocity is a Vector
    velocityVector = []

    for i in range(len(cx)):
        velocity = collection.objects[str(i)].matrix_world.col[2][:3]
        velocityVector.append((cx[i].co[0], velocity))

    return velocityVector

#-------------------------------------------------------------------------------

# function to update the values of the fcurve asignated to a custom property

def updateCustomVelocityProperty(action, customPropertyName, velocityVector):
    bpy.types.Object.velocity = bpy.props.FloatVectorProperty(name=customPropertyName)
    for i in range(3):      
        # Remove the previous fcurve
        v = action.fcurves.find(customPropertyName, index=i)
        if v is not None:
            action.fcurves.remove(v)
        # create a clean new fcurve

        action.fcurves.new(customPropertyName, index=i)
        v = action.fcurves.find(customPropertyName, index=i)

        # add all the KFs to the fcurve

        for kf in velocityVector:             
            v.keyframe_points.insert(kf[0], kf[1][i])

############################################################################################################
def get_pos (frame, interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia):
    
    cx = bpy.data.objects[object].animation_data.action.fcurves.find('location',index=0)
    cy = bpy.data.objects[object].animation_data.action.fcurves.find('location',index=1)
    cz = bpy.data.objects[object].animation_data.action.fcurves.find('location',index=2)
    if len(cx.keyframe_points) == 2:
        if frame >= cx.keyframe_points[0].co[0] and frame < cx.keyframe_points[1].co[0]:
            
            f_sig = cx.keyframe_points[1].co[0]
            pos_sig = (cx.keyframe_points[1].co[1], cy.keyframe_points[1].co[1], cz.keyframe_points[1].co[1])
            
            f_sig_sig = cx.keyframe_points[1].co[0]
            pos_sig_sig = (cx.keyframe_points[1].co[1], cy.keyframe_points[1].co[1], cz.keyframe_points[1].co[1])
            
            f_ant = cx.keyframe_points[0].co[0]
            pos_ant = (cx.keyframe_points[0].co[1], cy.keyframe_points[0].co[1], cz.keyframe_points[0].co[1])
            
            f_ant_ant = cx.keyframe_points[0].co[0]
            pos_ant_ant = (cx.keyframe_points[0].co[1], cy.keyframe_points[0].co[1], cz.keyframe_points[0].co[1])
            
        if frame > cx.keyframe_points[1].co[0] or frame < cx.keyframe_points[0].co[0] :
            return
    else:  
        for i in range(0, len(cx.keyframe_points) - 1):
            # Caso general
            if frame >= cx.keyframe_points[i].co[0] and frame < cx.keyframe_points[-2].co[0]:
                
                f_sig = cx.keyframe_points[i+1].co[0]
                pos_sig = (cx.keyframe_points[i+1].co[1], cy.keyframe_points[i+1].co[1], cz.keyframe_points[i+1].co[1])
                
                f_sig_sig = cx.keyframe_points[i+2].co[0]
                pos_sig_sig = (cx.keyframe_points[i+2].co[1], cy.keyframe_points[i+2].co[1], cz.keyframe_points[i+2].co[1])
                
                f_ant = cx.keyframe_points[i].co[0]
                pos_ant = (cx.keyframe_points[i].co[1], cy.keyframe_points[i].co[1], cz.keyframe_points[i].co[1])
                
                f_ant_ant = cx.keyframe_points[i-1].co[0]
                pos_ant_ant = (cx.keyframe_points[i-1].co[1], cy.keyframe_points[i-1].co[1], cz.keyframe_points[i-1].co[1])
            
            # Primer punto    
            if frame < cx.keyframe_points[1].co[0]:
                
                f_sig = cx.keyframe_points[1].co[0]
                pos_sig = (cx.keyframe_points[1].co[1], cy.keyframe_points[1].co[1], cz.keyframe_points[1].co[1])
                
                f_sig_sig = cx.keyframe_points[2].co[0]
                pos_sig_sig = (cx.keyframe_points[2].co[1], cy.keyframe_points[2].co[1], cz.keyframe_points[2].co[1])
                
                f_ant = cx.keyframe_points[0].co[0]
                pos_ant = (cx.keyframe_points[0].co[1], cy.keyframe_points[0].co[1], cz.keyframe_points[0].co[1])
               
                f_ant_ant = cx.keyframe_points[0].co[0]
                pos_ant_ant = (cx.keyframe_points[0].co[0], cy.keyframe_points[0].co[1], cz.keyframe_points[0].co[1])
            
            # Ultimo punto   
            if frame >= cx.keyframe_points[-2].co[0]:
                
                f_sig = cx.keyframe_points[-1].co[0]
                pos_sig = (cx.keyframe_points[-1].co[1], cy.keyframe_points[-1].co[1], cz.keyframe_points[-1].co[1])
                
                f_sig_sig = cx.keyframe_points[-1].co[0]
                pos_sig_sig = (cx.keyframe_points[-1].co[1], cy.keyframe_points[-1].co[1], cz.keyframe_points[-1].co[1])
                
                f_ant = cx.keyframe_points[-2].co[0]
                pos_ant = (cx.keyframe_points[-2].co[1], cy.keyframe_points[-2].co[1], cz.keyframe_points[-2].co[1])
                
                f_ant_ant = cx.keyframe_points[-3].co[0]
                pos_ant_ant = (cx.keyframe_points[-3].co[1], cy.keyframe_points[-3].co[1], cz.keyframe_points[-3].co[1])
                
                
            if frame > cx.keyframe_points[-1].co[0] or frame < cx.keyframe_points[0].co[0] :
                return
            
    interpola_valores(frame, f_ant, f_sig, f_ant_ant, f_sig_sig, pos_ant_ant,pos_ant,pos_sig,pos_sig_sig, interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia, 0)
    interpola_valores(frame, f_ant, f_sig, f_ant_ant, f_sig_sig, pos_ant_ant,pos_ant,pos_sig,pos_sig_sig, interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia, 1)
    interpola_valores(frame, f_ant, f_sig, f_ant_ant, f_sig_sig, pos_ant_ant,pos_ant,pos_sig,pos_sig_sig, interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia, 2)
    
############################################################################################################

 
class MyProperties(bpy.types.PropertyGroup):
    aleatorio: bpy.props.BoolProperty(
        name = "Random",
        description = "Create random movement",
        default = False
        )
    tipo: bpy.props.EnumProperty(
        name = "Type of interpolation:",
        description = "Choose the type of interpolation",
        items = [ ('Lineal', "Lineal", ""),
                ('Hermite', "Hermite", ""),
                ('Catmull-Rom', "Catmull-Rom", ""),
               ]
        )
    ins_frames: bpy.props.IntProperty(
        name = "Frames periodicity",
        description = "How frequently do we insert key frames",
        min = 1,
        default = 3
        )
    amplitud: bpy.props.FloatProperty(
        name = "Amplitude",
        default = 0.5,
        min = 0.01
        )
    frecuencia: bpy.props.FloatProperty(
        name = "Frequency",
        default = 0.25,
        min = 0.01,
        max = 10
        )
    tau: bpy.props.FloatProperty(
        name = "Tau",
        default = 0.3,
        min = 0.01
        )
        
def CopRuta(ini_obj, list):
    """Esta función copia la trayectoria de un objeto a una lista de objetos."""
    
    kf_listx = bpy.data.objects[ini_obj].animation_data.action.fcurves.find('location', index = 0).keyframe_points[:]
    kf_listy = bpy.data.objects[ini_obj].animation_data.action.fcurves.find('location', index = 1).keyframe_points[:]
    kf_listz = bpy.data.objects[ini_obj].animation_data.action.fcurves.find('location', index = 2).keyframe_points[:]
    kf_numb = len(kf_listx)
    
    for ob in list:
        
        if bpy.data.objects[ob].animation_data:
            
            bpy.data.objects[ob].animation_data_clear();
            
        for j in range(0, kf_numb):
            
            bpy.context.scene.frame_set(kf_listx[j].co[0]);
            bpy.data.objects[ob].location[0] = kf_listx[j].co[1];
            bpy.data.objects[ob].location[1] = kf_listy[j].co[1];
            bpy.data.objects[ob].location[2] = kf_listz[j].co[1];
            bpy.data.objects[ob].keyframe_insert(data_path = "location");       
        
class ModifyTrayectoria(bpy.types.Operator):
    bl_idname = 'movement.modify'
    bl_label = 'Modify'
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) == 0:
            return False

        for ob in context.selected_objects:
            if ob.animation_data is None:
                return False
        for ob in context.selected_objects:
            if ob.animation_data.action is None:
                return False
        for ob in context.selected_objects:
            if len(ob.animation_data.action.fcurves.find('location', index = 0).keyframe_points) < 2:
                return False
        return True

    
    def invoke(self, context, event):
        scene = context.scene
        mytool = scene.my_tool
        
        start = bpy.data.scenes['Scene'].frame_start
        fin = bpy.data.scenes['Scene'].frame_end    
            
        tau = mytool.tau;
        aleatorio = mytool.aleatorio
        fr_ins = mytool.ins_frames
        frecuencia = mytool.frecuencia
        interpolacion = mytool.tipo
        amplitud = mytool.amplitud
        
        
        for object in bpy.context.selected_objects:
            if interpolacion == 'Hermite':
                actionName = object.animation_data.action.name
                action = bpy.data.actions[actionName]
                velocityVector = createEmptiesAndGetVelocityVector(action)
                updateCustomVelocityProperty(action, 'velocity', velocityVector)
            for frame in range(start, fin + 1, fr_ins):
                get_pos (frame, interpolacion, object.name, tau, amplitud, aleatorio, frecuencia)
            
        return {"FINISHED"}
  
class Interpolation(bpy.types.Panel):
    bl_idname = "panel.trayectoria"
    bl_label = "Trayectoria"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    # bl_category = "Tools"
    bl_category = "Movimiento"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        layout.prop(mytool, "aleatorio")
        layout.prop(mytool, 'tipo')
        layout.prop(mytool, "ins_frames")
        if not mytool.aleatorio:
            sub = layout.row() 
            sub.enabled = False
            sub.prop(mytool, 'amplitud')
            sub = layout.row() 
            sub.enabled = False
            sub.prop(mytool, 'frecuencia')
        else:
            layout.prop(mytool, "amplitud")
            layout.prop(mytool, 'frecuencia')
        if not mytool.tipo == "Catmull-Rom":
            sub = layout.row() 
            sub.enabled = False
            sub.prop(mytool, 'tau')
        else:
            layout.prop(mytool, 'tau')
        self.layout.operator("movement.modify", icon='CURVE_PATH', text="Interpolate")

def register() :
    bpy.utils.register_class(ModifyTrayectoria)
    bpy.utils.register_class(Interpolation)
    bpy.utils.register_class(MyProperties)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)
 
def unregister() :
    bpy.utils.unregister_class(ModifyTrayectoria)
    bpy.utils.unregister_class(Interpolation)

register()

    
    
    
    
    
