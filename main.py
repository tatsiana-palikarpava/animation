#    Addon info
bl_info = {
    'name': 'Interpolation',
    'author': 'Marc Guerrero Palanca, Tatsiana Palikarpava, Alberto Pérez Abad',
    'location': 'View3D > Tools > Movimiento',
    'category': 'Movement'
    }
 
import bpy
import numpy as np
import math as m
import random
from mathutils import Vector
   
############################################################################################################    
""" Constructs a table of entities [f, l] which indicate that by frame f an object have run a part
 of the trajectory of length l """
def construir_tabla(h, ini, fin,interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia):
    tabla = [[ini, 0]]
    L = 0
    pos = get_pos(ini, interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia)
    for frm in range(ini + 1, fin + 1, h):
        pos_ant = pos
        # calculate new position
        pos = get_pos(frm, interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia)
        # covered distance
        d = m.sqrt((pos[0] - pos_ant[0])*(pos[0] - pos_ant[0]) + (pos[1] - pos_ant[1])*(pos[1] - pos_ant[1])+(pos[2] - pos_ant[2])*(pos[2] - pos_ant[2]))
        L += d
        tabla.append([frm , L])
    return tabla, L

############################################################################################################ 

""" Implements search in the table. Returns a frame where an object have run a part
 of the trajectory of length l """
def busca(l, tabla, ini, fin):
    if l < tabla[0][1]:
        return tabla[0][0]
    if l > tabla[-1][1]:
        return tabla[-1][0]
    # we store covered length of the curve and frame value
    curr_l = 0
    curr_f = ini
    found = False
    for i in range(0, len(tabla) + 1):
        # updating values
        curr_f = tabla[i][0]
        curr_l = tabla[i][1]
        
        if curr_l == l:
            # entity found
            found = True
            break
        if curr_l > l:
            # current length is bigger than required -> not found
            break
        # else continue search
        
    if found:
        return curr_f
    else:
        # if entity is not found apply linear interpolation
        u = (l - tabla[i - 1][1])/(curr_l - tabla[i - 1][1])
        return lineal(u, tabla[i - 1][0], curr_f)
 
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
        
        pos += aumento
        
        return pos
    
    
###################################################################################################################    
def lineal (u, pos1, pos2):
    """Interpolación lineal utilizando la posición del fotograma clave anterior y la posición del fotograma clave siguiente
     y el coeficiente u entre 0 y 1"""
     
    pos = pos1 + u * (pos2 - pos1)
    
    return pos

    
def hermite(u, pos1, pos2, vel1, vel2):
    """ Hermite interpolation, which uses the positions in previous and next keyframes and velocities, calculated using keyframe before previos and after next"""
    pos = (1 - 3 * pow(u, 2) + 2 * pow(u, 3)) * pos1 + pow(u, 2) * (3 - 2 * u) * pos2 + u * (u - 1)* (u - 1) * vel1 + pow(u, 2) * (u - 1) * vel2
    
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

    PHI = m.radians(random.randint(0,360));
    
    # Apmlitude de la onda en el eje
    Amplitude = random.uniform(0,Amplitude_Max);
    
    Aumento = Amplitude * m.sin( frecuencia * frame + PHI);

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
    """ Get position of the object at the current frame with user defined type of interpolation"""
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
                break
            
    posx = interpola_valores(frame, f_ant, f_sig, f_ant_ant, f_sig_sig, pos_ant_ant,pos_ant,pos_sig,pos_sig_sig, interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia, 0)
    posy = interpola_valores(frame, f_ant, f_sig, f_ant_ant, f_sig_sig, pos_ant_ant,pos_ant,pos_sig,pos_sig_sig, interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia, 1)
    posz = interpola_valores(frame, f_ant, f_sig, f_ant_ant, f_sig_sig, pos_ant_ant,pos_ant,pos_sig,pos_sig_sig, interpolacion, object, tau, Amplitude_Max, aleatorio, frecuencia, 2)
    
    pos = [posx, posy, posz]
    
    return pos
 
############################################################################################################
""" Class for creating add-on menu """ 
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
    vel_control: bpy.props.BoolProperty(
        name = "Control of velocity",
        description = "Enable velocity control",
        default = False
        )
    camb: bpy.props.BoolProperty(
        name = "Extend timeline",
        description = "Once checked, changes length of timeline",
        default = False
        )
    aplica_reparam: bpy.props.BoolProperty(
        name = "Reparametrization",
        description = "Apply reparametrization",
        default = False
        )
    distancia_actual: bpy.props.FloatProperty(
        name = "Current distance",
        default = 0
        )
    orientation: bpy.props.BoolProperty(
        name = "Orientation",
        description = "Orientate an object during trajectory calculation",
        default = False
        )
    axis: bpy.props.EnumProperty(
        name = "Axis",
        description = "Choose the axis",
        items = [ ('X', "X", ""),
                ('Y', "Y", ""),
                ('Z', "Z", ""),
                ('-X', "-X", ""),
                ('-Y', "-Y", ""),
                ('-Z', "-Z", "")
               ]
        )
    lateral: bpy.props.EnumProperty(
        name = "Lateral axis",
        description = "Choose the axis",
        items = [ ('X', "X", ""),
                ('Y', "Y", ""),
                ('Z', "Z", ""),
                ('-X', "-X", ""),
                ('-Y', "-Y", ""),
                ('-Z', "-Z", "")
               ]
        )
    tilt: bpy.props.BoolProperty(
        name = "Tilt",
        description = "Include lateral tilt",
        default = False
        )
    angle: bpy.props.FloatProperty(
        name = "Rotation angle",
        default = 0,
        max = 180
        )
############################################################################################################       
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
############################################################################################################
        
class ModifyTrayectoria(bpy.types.Operator):
    bl_idname = 'movement.modify'
    bl_label = 'Modify'
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        """Prevent errors caused by incompatible parameters or not complete data"""
        # No objects selected
        if len(context.selected_objects) == 0:
            return False
        # No animation data
        for ob in context.selected_objects:
            if ob.animation_data is None:
                return False
        # No action
        for ob in context.selected_objects:
            if ob.animation_data.action is None:
                return False
        # No location fcurve
        for ob in context.selected_objects:
            if ob.animation_data.action.fcurves.find('location', index = 0) is None:
                return False
        # No location keyframes
        for ob in context.selected_objects:
            if len(ob.animation_data.action.fcurves.find('location', index = 0).keyframe_points) < 2:
                return False
        scene = context.scene
        mytool = scene.my_tool
        vel_control = mytool.vel_control
        aplica_reparam = mytool.aplica_reparam
        # Current distance not defined
        if vel_control and aplica_reparam:
            for ob in context.selected_objects:
                if ob.animation_data.action.fcurves.find('distance.distancia_actual') is None:
                    return False
        # Incorrect axes choosed
        if mytool.orientation:
            if mytool.axis == mytool.lateral or (str(mytool.axis) == str('-' + str(mytool.lateral)))  or (str(mytool.lateral) == str('-' + str(mytool.axis))):
                return False
            
        return True

    
    def invoke(self, context, event):
        """ Launch modifying process by clicking button Interpolate"""
        scene = context.scene
        mytool = scene.my_tool
        
        start = bpy.data.scenes['Scene'].frame_start
        fin = bpy.data.scenes['Scene'].frame_end    
            
        # obtaining user-defined parameters from the tool    
        tau = mytool.tau;
        aleatorio = mytool.aleatorio
        fr_ins = mytool.ins_frames
        frecuencia = mytool.frecuencia
        interpolacion = mytool.tipo
        amplitud = mytool.amplitud
        
        vel_control = mytool.vel_control
        cambiar = mytool.camb
        aplica_reparam = mytool.aplica_reparam
        
        orientation = mytool.orientation
        axis = mytool.axis
        lat = mytool.lateral
    
        positions = []
        for object in bpy.context.selected_objects:
            if interpolacion == 'Hermite':
                actionName = object.animation_data.action.name
                action = bpy.data.actions[actionName]
                velocityVector = createEmptiesAndGetVelocityVector(action)
                updateCustomVelocityProperty(action, 'velocity', velocityVector)
                
            start = (int)(object.animation_data.action.fcurves.find('location', index = 0).keyframe_points[0].co[0])
            fin = (int)(object.animation_data.action.fcurves.find('location', index = 0).keyframe_points[-1].co[0])
            print(start)
            print(fin)
            nuevo_fin = fin 
              
            if vel_control:
                #constructing a table
                tabla,lmax = construir_tabla(fr_ins, start, fin, interpolacion, object.name, tau, amplitud, aleatorio, frecuencia)
              
                nuevo_fin = fin
                if aplica_reparam:
                    # block timeline extension option
                    cambiar = False
                if cambiar:
                    # extend timeline
                    nuevo_fin = m.floor(lmax*24)
            for frame in range(start, nuevo_fin + 1, fr_ins):
                
                if vel_control:
                    if aplica_reparam:
                        context.scene.frame_set(frame)
                        # obtain desired length from the tool
                        long_deseada = object.distance.distancia_actual
                        
                    else:
                        if cambiar:
                            # setting desired length manually (velocity = 1 un./s)
                            t = frame / 24
                            long_deseada = t
                        else:
                            # setting desired length manually (velocity is adapted to the length of timeline)
                            long_deseada = frame/nuevo_fin*lmax
                    frm_old = busca(long_deseada, tabla, start, fin)
                else:
                    frm_old = frame
                
                p = get_pos (frm_old, interpolacion, object.name, tau, amplitud, aleatorio, frecuencia)
                positions.append([frame, p])
     
        bpy.data.scenes["Scene"].frame_end = nuevo_fin
        # removing old keyframes
        object.animation_data.action.fcurves.remove(object.animation_data.action.fcurves.find('location',index = 0))
        object.animation_data.action.fcurves.remove(object.animation_data.action.fcurves.find('location',index = 1))
        object.animation_data.action.fcurves.remove(object.animation_data.action.fcurves.find('location',index = 2))
        #inserting new keyframes
        for pos in positions:
            bpy.context.scene.frame_set(pos[0]);
            bpy.data.objects[object.name].location[0] = pos[1][0]
            bpy.data.objects[object.name].location[1] = pos[1][1]
            bpy.data.objects[object.name].location[2] = pos[1][2]
            bpy.data.objects[object.name].keyframe_insert(data_path = "location");
    
        loc_x_curve = bpy.data.objects[object.name].animation_data.action.fcurves.find('location', index = 0)
        loc_y_curve = bpy.data.objects[object.name].animation_data.action.fcurves.find('location', index = 1)
        loc_z_curve = bpy.data.objects[object.name].animation_data.action.fcurves.find('location', index = 2)
        # Enable linear interpolation between inserted keyframes (necessary when fr_ins > 1)
        for k in loc_x_curve.keyframe_points:
            k.interpolation = 'LINEAR'
        for k in loc_y_curve.keyframe_points:
            k.interpolation = 'LINEAR'
        for k in loc_z_curve.keyframe_points:
            k.interpolation = 'LINEAR'
            
        # Apply orientation control    
        if orientation:
            start = bpy.data.scenes['Scene'].frame_start
            end = bpy.data.scenes['Scene'].frame_end   
            # Use quaternion rotation 
            object.rotation_mode = 'QUATERNION'
            # remove old rotation data
            if object.animation_data.action.fcurves.find('rotation_quaternion') != None:
                object.animation_data.action.fcurves.remove(object.animation_data.action.fcurves.find('rotation_quaternion', index = 0))
                object.animation_data.action.fcurves.remove(object.animation_data.action.fcurves.find('rotation_quaternion', index = 1))
                object.animation_data.action.fcurves.remove(object.animation_data.action.fcurves.find('rotation_quaternion', index = 2))
                object.animation_data.action.fcurves.remove(object.animation_data.action.fcurves.find('rotation_quaternion', index = 3))
            
            for frm in range(start, end + 1, fr_ins):
                if frm != end - 1:
                    bpy.context.scene.frame_set(frm)
                    # Obtain current position
                    loc_ant = Vector([object.location.x,object.location.y,object.location.z])
                    # Obtain nextt position
                    bpy.context.scene.frame_set(frm + 1)
                    loc_sig = Vector([object.location.x,object.location.y,object.location.z])
                    
                else:
                    # For the last frame we use previous rotation
                    bpy.context.scene.frame_set(frm - 1)
                    loc_ant = Vector([object.location.x,object.location.y,object.location.z])
                    bpy.context.scene.frame_set(frm)
                    loc_sig = Vector([object.location.x,object.location.y,object.location.z])
                # Calculating tangent vector
                t = Vector([loc_sig[0] - loc_ant[0], loc_sig[1] - loc_ant[1], loc_sig[2] - loc_ant[2]])
                bpy.context.scene.frame_set(frm)
                if t.magnitude != 0:
                    # Location changed
                    if mytool.tilt:
                        q = get_quat_rot(axis, t, lat, object.angle_lat.angle/180*2*m.pi)
                    else:
                        q = get_quat_rot(axis, t, lat, 0)
                else:
                    # Location didn't change, use previous rotation quaternion
                    bpy.context.scene.frame_set(frm - 1)
                    q = object.rotation_quaternion
                    bpy.context.scene.frame_set(frm)
                object.rotation_quaternion = q
                object.keyframe_insert(data_path ='rotation_quaternion')
               
                if fr_ins > 1 and frm != start:
                    # Apply Slerp for intermediate frames between keyframes to get smoother rotation
                    bpy.context.scene.frame_set(frm - fr_ins)
                    q0 = object.rotation_quaternion
                    for f in range(frm - fr_ins + 1, frm):
                        # Also it is possible to use our version of slerp
                        #q_i = slerp(q0, q, (f - frm + fr_ins)/fr_ins)
                        q_i = q0.slerp(q, (f - frm + fr_ins)/fr_ins)
                        bpy.context.scene.frame_set(f)
                        object.rotation_quaternion = q_i
                        object.keyframe_insert(data_path ='rotation_quaternion')
                        
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
        if len(bpy.context.selected_objects) != 0:
            dist = bpy.context.selected_objects[0].distance
            angle = bpy.context.selected_objects[0].angle_lat
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
            layout.prop(mytool, "vel_control")
            if not mytool.vel_control:
                sub = layout.column() 
                sub.enabled = False
                sub.prop(mytool, 'camb')
                sub.prop(mytool, 'aplica_reparam')
                sub.prop(dist,'distancia_actual')
            else:
                if mytool.camb:
                    layout.prop(mytool, "camb")
                    sub = layout.column()
                    sub.enabled = False
                    sub.prop(mytool, 'aplica_reparam')
                    sub.prop(dist,'distancia_actual')
                else:
                    if not mytool.aplica_reparam:
                        layout.prop(mytool, "camb")
                        layout.prop(mytool, 'aplica_reparam')
                        sub = layout.row()
                        sub.enabled = False
                        sub.prop(dist,'distancia_actual')
                    else:
                        sub = layout.row()
                        sub.enabled = False
                        sub.prop(mytool, "camb")
                        layout.prop(mytool, 'aplica_reparam')
                        layout.prop(dist,'distancia_actual')
            
            layout.prop(mytool, "orientation")
            if not mytool.orientation:
                sub = layout.column()
                sub.enabled = False
                sub.prop(mytool, "axis")
                sub.prop(mytool, "lateral")
                sub.prop(mytool, "tilt")
                if not mytool.tilt:
                    subsub = layout.column()
                    subsub.enabled = False
                    subsub.prop(angle, "angle")
                else:
                    sub.prop(angle, "angle")
            else:
                layout.prop(mytool, "axis")
                layout.prop(mytool, "lateral")
                layout.prop(mytool, "tilt")
                if not mytool.tilt:
                    subsub = layout.column()
                    subsub.enabled = False
                    subsub.prop(angle, "angle")
                else:
                    layout.prop(angle, "angle")
            self.layout.operator("movement.modify", icon='CURVE_PATH', text="Interpolate")



def register() :
    bpy.utils.register_class(ModifyTrayectoria)
    bpy.utils.register_class(Interpolation)
    bpy.utils.register_class(MyProperties)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)
    bpy.types.Object.distance = bpy.props.PointerProperty(type=MyProperties)
    bpy.types.Object.angle_lat = bpy.props.PointerProperty(type=MyProperties)
def unregister() :
    bpy.utils.unregister_class(ModifyTrayectoria)
    bpy.utils.unregister_class(Interpolation)

register()



#######################################################################################
""" Quaternion operations"""
from mathutils import Quaternion

def slerp(q1, q2, u):
    """ Get quaternion by slerp with factor u"""
    cos_ang = q1.dot(q2)
    if (cos_ang < -1):
        cos_ang = -1
    if (cos_ang > 1):
        cos_ang = 1
    ang = m.acos(cos_ang)
    sin_ang = m.sin(ang)
    if (sin_ang != 0):
        q = m.sin(ang * (1 - u))/sin_ang * q1 + m.sin(ang * u)/sin_ang * q2
    else:
        q = q1
    return q

def get_quat_from_vecs(e, t):
    """ Align vector e with t""" 
    v = e.cross(t)
    cos_ang = e.dot(t)
    if v.magnitude > 0:
        v = v.normalized()
        if (cos_ang < -1):
            cos_ang = -1
        if (cos_ang > 1):
            cos_ang = 1
        ang = m.acos(cos_ang)
        q = Quaternion([m.cos(ang/2), v[0]*m.sin(ang/2),v[1]*m.sin(ang/2),v[2]*m.sin(ang/2)])    
    else:
        # If already aligned or oppositely directed      
        if cos_ang <= -1:
            q = Quaternion([0,0,0,1])
        else:
            q = Quaternion([1,0,0,0])
        
    return q

def get_lat_vec(t):
    """ Obtain vector which is perpendicular to the Z axis and tangent vector """
    t = t.normalized()
    e_l = Vector([0, 0, 1])
    l = e_l.cross(t)
    l = l.normalized()
    return l
 

def get_quat_rot(dir, vec, lat, theta):
    """ Align the object with user defined parameters"""
    # Define the direction to be aligned with tangent vector
    if dir == 'X':
        e = Vector([1, 0, 0])
    elif dir == 'Y':
        e = Vector([0, 1, 0])
    elif dir == 'Z':
        e = Vector([0, 0, 1])
    elif dir == '-X':
        e = Vector([-1, 0, 0])
    elif dir == '-Y':
        e = Vector([0, -1, 0])
    else:
        e = Vector([0, 0, -1])
    # Define the lateral axis
    if lat == 'X':
        e_l = Vector([1, 0, 0])
    elif lat == 'Y':
        e_l = Vector([0, 1, 0])
    elif lat == 'Z':
        e_l = Vector([0, 0, 1])
    elif lat == '-X':
        e_l = Vector([-1, 0, 0])
    elif lat == '-Y':
        e_l = Vector([0, -1, 0])
    else:
        e_l = Vector([0, 0, -1])
    # Normalize tangent vector
    vec = vec.normalized()
    # Align the main direction
    q = get_quat_from_vecs(e, vec) 
    
    # Get lateral vector
    l = get_lat_vec(vec)
    e_l.rotate(q) 
    
    # Make lateral axis horizontal
    q2 = get_quat_from_vecs(e_l, l) 
    q2 = q2.cross(q)
    # Apply lateral tilt
    q3 = Quaternion([m.cos(theta/2), vec[0]*m.sin(theta/2),vec[1]*m.sin(theta/2),vec[2]*m.sin(theta/2)])
    q3 = q3.cross(q2)
    return q3
