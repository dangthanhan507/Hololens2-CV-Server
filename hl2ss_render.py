#------------------------------------------------------------------------------
# hl2ss_render.py
# 
# This is hl2ss wrapper for rendering on the hololens visor. This will allow
# us to start/stop rendering software for the visor and also render any 
# primitive we want on the visor with access to color, primitives, and 
# transform. 
#------------------------------------------------------------------------------

from hl2ss_stream import HOST_IP, ROOT_PATH
import os
import sys
sys.path.append(os.path.join(ROOT_PATH,'hl2ss','viewer'))

import hl2ss
import hl2ss_rus

def getObjectType(object):
    if object == "cube":
        return hl2ss_rus.PrimitiveType.Cube
    elif object == "capsule":
        return hl2ss_rus.PrimitiveType.Capsule
    elif object == "cylinder":
        return hl2ss_rus.PrimitiveType.Cylinder
    elif object == "sphere":
        return hl2ss_rus.PrimitiveType.Sphere
    elif object == "plane":
        return hl2ss_rus.PrimitiveType.Plane
    elif object == "quad":
        return hl2ss_rus.PrimitiveType.Quad

class RenderObject:
    def __init__(self, object, pos ,rot, scale, rgba):
        '''
            pos: list size 3 [x,y,z]
            rot: quaternion list size 4 [x,y,z,w]
            scale: list size 3 [sx,sy,sz]
            rgba: list size 4 [r,g,b,a]
        '''
        self.object = getObjectType(object)
        self.pos = pos
        self.rot = rot #quaternion
        self.scale = scale
        self.rgba = rgba

#NOTE: look at hl2ss_rus for primitives
#NOTE: plane primitive has issues
class Hl2ssRender:
    def __init__(self):
        self.objs = []
        self.ipc = hl2ss.ipc_umq(HOST_IP, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)

    def start(self):
        self.ipc.open()
    def stop(self):
        self.ipc.close()

    def addPrimObject(self, object, pos, rot, scale, rgba):
        display_list = hl2ss_rus.command_buffer()
        display_list.begin_display_list()

        #create obj
        display_list.create_primitive(getObjectType(object))
        display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast)
        display_list.set_world_transform(0, pos, rot, scale)
        display_list.set_color(0, rgba)
        display_list.set_active(0, hl2ss_rus.ActiveState.Active)
        display_list.end_display_list()

        self.ipc.push(display_list)
        results = self.ipc.pull(display_list)

        self.objs.append(results[1])
        return results[1]
    
    def addPrimObjects(self, render_objects):
        '''
            render_objects: list of RenderObjects
        '''
        display_list = hl2ss_rus.command_buffer()
        display_list.begin_display_list() #cmd 0

        cmd_idxs = list(range(1,1+5*len(render_objects),5)) # 1, 6, 11,.... listing all idx of added obj
        for i in range(len(render_objects)):
            render_obj = render_objects[i]
            pos = render_obj.pos
            rot = render_obj.rot
            scale = render_obj.scale
            rgba = render_obj.rgba
            objType = render_obj.object

            display_list.create_primitive(objType) # cmd 1 + 5*i
            display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast)
            display_list.set_world_transform(0, pos, rot, scale)
            display_list.set_color(0, rgba)
            display_list.set_active(0, hl2ss_rus.ActiveState.Active)
        self.ipc.push(display_list)
        results = self.ipc.pull(display_list)

        object_ids = [results[idx] for idx in cmd_idxs ]
        self.objs = self.objs + object_ids

        return object_ids

    
    def removePrimObject(self, object_id):
        if object_id in self.objs:
            self.objs.remove(object_id)

            display_list = hl2ss_rus.command_buffer()
            display_list.begin_display_list()
            display_list.remove(object_id)
            display_list.remove_display_list()
            self.ipc.push(display_list)



    def clear(self):
        display_list = hl2ss_rus.command_buffer()
        display_list.begin_display_list()
        display_list.remove_all()
        display_list.end_display_list()
        self.ipc.push(display_list)
        self.objs = []
