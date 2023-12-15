import bpy
from bpy.types import ( PropertyGroup ,Operator, UIList)
from bpy.app.handlers import persistent
import imp


from bpy.props import(
    PointerProperty,
    IntProperty,
    StringProperty,
    CollectionProperty,
    BoolProperty,
    EnumProperty,
    )

from . import utils
from . import cmd_
from . import apply

imp.reload(utils)
imp.reload(cmd_)
imp.reload(apply)

bl_info = {
"name": "CyaCollectionEditor",
"author": "Takehito Tsuchiya",
"version": (0, 3.24),
"blender": (2, 90, 1),
"location" : "CYA",
"description": "cyatools",
"category": "Object"}


class CYACOLLECTIONEDITOR_Props_OA(PropertyGroup):
    apply_frame : IntProperty(name="apply_frame")

    currentindex : IntProperty()
    rename_string : StringProperty()
    replace_string : StringProperty()
    prefix_underbar : BoolProperty(default = True)

    blendshape_apply : BoolProperty(default = False,name="blendshape")
    delete_prefix : BoolProperty(default = False,name="delete prefix")

    word : EnumProperty(items= (
        ('none', 'none', 'none'),
        ('00_Model', '00_Model', '00_Model'),
        ('High', 'High', 'High'),
        ('Low', 'Low', 'Low')
        ))

#---------------------------------------------------------------------------------------
#
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_UL_uilist(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:


            layout.prop(item, "bool_val", text = "")
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)


        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

#---------------------------------------------------------------------------------------
#
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_PT_collectioneditor(utils.panel):
    bl_label = "Collection Editor"
    bl_category = "CYA"
    bl_idname = "CYACOLLECTIONEDITOR_PT_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        ui_list = context.window_manager.cyacollectioneditor_list
        props = bpy.context.scene.cyacollectioneditor_oa

        layout=self.layout
        row = layout.row()
        col = row.column()

        col.template_list("CYACOLLECTIONEDITOR_UL_uilist", "", ui_list, "itemlist", ui_list, "active_index", rows=8)
        col = row.column(align=True)

        # col.operator("cyaobjectlist.select_all", icon='PROP_CON')
        col.operator("cyacollectioneditor.add", icon='FILE_REFRESH')
        # col.operator("cyaobjectlist.remove", icon=utils.icon['REMOVE'])
        # col.operator("cyaobjectlist.move_item", icon=utils.icon['UP']).dir = 'UP'
        # col.operator("cyaobjectlist.move_item", icon=utils.icon['DOWN']).dir = 'DOWN'
        # col.operator("cyaobjectlist.clear", icon=utils.icon['CANCEL'])
        # col.operator("cyaobjectlist.remove_not_exist", icon='ERROR')

        array = (
        ('show','HIDE_OFF'),
        ('hide','HIDE_ON'),
        # ('select','RESTRICT_SELECT_ON'),
        # ('selected','DECORATE_LIBRARY_OVERRIDE'),
        # ('invert','HOLDOUT_ON')
        )

        row = layout.row(align=True)

        row.label( icon = "CHECKMARK" )
        for i,x in enumerate(array):
            row.operator("cyacollectioneditor.check_item",icon = x[1] ).op = i

        row.label( icon = "DOT" )
        row.label( icon = "RESTRICT_SELECT_OFF" )

        for i,x in enumerate(array):
            row.operator("cyacollectioneditor.check_item",icon = x[1] ).op = i+2


        row = layout.row(align=True)
        row.operator("cyacollectioneditor.rename")#リネームのウインドウを表示

        row = layout.row(align=True)
        row.label( text = 'apply collection' )
        #row.operator("cyatools.apply_model" , icon='OBJECT_DATAMODE' )
        row.operator("cyacollectioneditor.apply_collection" , icon='GROUP' ,text = 'active').mode = 0
        row.operator("cyacollectioneditor.apply_collection" , icon='GROUP' ,text = 'checked').mode = 1

        row = layout.row(align=True)
        row.prop(props, "apply_frame")
        row.prop(props, "blendshape_apply")
        row.prop(props, "delete_prefix")


        #row.operator("cyatools.apply_collection_instance" , icon='GROUP' )
        #row.operator("cyatools.apply_particle_instance", icon='PARTICLES' )



#---------------------------------------------------------------------------------------
#リネームツール
#リネームとオブジェクト選択に関するツール群
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_MT_rename(Operator):
    bl_idname = "cyacollectioneditor.rename"
    bl_label = "rename tool"

    def execute(self, context):
        return{'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self , width = 400 )

    def draw(self, context):
        props = bpy.context.scene.cyacollectioneditor_oa
        layout=self.layout

        row = layout.row()
        col = row.column()
        box = col.box()
        box.prop(props, "rename_string" , text = 'word')
        box.prop(props, "replace_string", text = 'replace')

        row1 = box.row()
        row1.operator("cyacollectioneditor.rename_add_sequential_number" , icon = 'LINENUMBERS_ON')
        row1.operator("cyacollectioneditor.rename_replace" )
        row1.operator("cyacollectioneditor.rename_add_word" , text = 'add prefix').mode = 'prefix'
        row1.operator("cyacollectioneditor.rename_add_word" , text = 'add suffix').mode = 'suffix'
        row1.prop(props, "prefix_underbar" , text = '_')


        box1 = box.box()
        box1.prop(props, "word")
        row1 =  box1.row()
        row1.operator("cyacollectioneditor.rename_add_word" , text = 'add prefix').mode = 'prefix_list'
        row1.operator("cyacollectioneditor.rename_add_word" , text = 'add suffix').mode = 'suffix_list'


        # box.operator("cyaobjectlist.rename_bonecluster")
        # box.operator("cyaobjectlist.rename_add_sequential_number" , icon = 'LINENUMBERS_ON')


        # box = col.box()
        # box.label(text = 'reneme finger')
        # row0 = box.row()
        # row0.operator("cyaobjectlist.rename_finger" , text = 'hand').mode = 0
        # row0.operator("cyaobjectlist.rename_finger" , text = 'foot').mode = 1
        # row0.prop(props, "finger_step")

        # box = row.box()
        # box.label(text = 'for UE4')
        # for p in ('clavile_hand' ,'arm_twist' , 'thigh_toe' ,'leg_twist', 'pelvis_spine' , 'neck_head' , 'finger'):
        #     box.operator("cyaobjectlist.rename_bonechain_ue4" , text = p).pt = p
        # box.prop(props, "setupik_lr", expand=True)



#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_OT_add(Operator):
    """選択を追加"""
    bl_idname = "cyacollectioneditor.add"
    bl_label = ""
    def execute(self, context):
        cmd_.add()
        return {'FINISHED'}


#---------------------------------------------------------------------------------------
#アプライ
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_OT_apply_collection(Operator):
    """選択を追加"""
    bl_idname = "cyacollectioneditor.apply_collection"
    bl_label = "col"
    mode : IntProperty()
    def execute(self, context):
        apply.apply_collection(self.mode)
        return {'FINISHED'}



#---------------------------------------------------------------------------------------
#rename tools
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_OT_rename_add_sequential_renumber(Operator):
    """コレクションを番号をつけてリネーム"""
    bl_idname = "cyacollectioneditor.rename_add_sequential_number"
    bl_label = ""
    def execute(self, context):
        cmd_.rename_add_sequential_number()
        return {'FINISHED'}


class CYACOLLECTIONEDITOR_OT_rename_add_word(Operator):
    """add word"""
    bl_idname = "cyacollectioneditor.rename_add_word"
    bl_label = ""
    mode : StringProperty()
    def execute(self, context):
        cmd_.rename_add_word(self.mode)
        return {'FINISHED'}


class CYACOLLECTIONEDITOR_OT_rename_replace(Operator):
    """Replace"""
    bl_idname = "cyacollectioneditor.rename_replace"
    bl_label = "replace"
    def execute(self, context):
        cmd_.rename_replace()
        return {'FINISHED'}

# class CYACOLLECTIONEDITOR_OT_rename_replace(Operator):
#     """Replace"""
#     bl_idname = "cyacollectioneditor.check_item"
#     bl_label = ""
#     def execute(self, context):
#         cmd_.rename_replace()
#         return {'FINISHED'}

class CYAOBJECTLIST_OT_check_item(Operator):
    """チェックされたアイテムの操作
1:表示　2:非表示　3:選択　4:選択中のものにチェック　5:反転"""
    bl_idname = "cyacollectioneditor.check_item"
    bl_label = ""
    op : IntProperty()
    def execute(self, context):
        cmd_.check_item(self.op)
        return {'FINISHED'}


#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_Props_item(PropertyGroup):
    name : StringProperty()
    bool_val : BoolProperty()

bpy.utils.register_class(CYACOLLECTIONEDITOR_Props_item)

class CYACOLLECTIONEDITOR_Props_list(PropertyGroup):
    active_index : IntProperty( update = cmd_.selection_changed )#リストの選択をした時
    itemlist : CollectionProperty(type=CYACOLLECTIONEDITOR_Props_item)#アイテムプロパティの型を収めることができるリストを生成



classes = (
    CYACOLLECTIONEDITOR_Props_OA,
    CYACOLLECTIONEDITOR_PT_collectioneditor,
    CYACOLLECTIONEDITOR_UL_uilist,
    CYACOLLECTIONEDITOR_Props_list,
    CYACOLLECTIONEDITOR_OT_add,
    CYACOLLECTIONEDITOR_MT_rename,
    CYACOLLECTIONEDITOR_OT_rename_add_sequential_renumber,

    CYACOLLECTIONEDITOR_OT_rename_add_word,
    CYACOLLECTIONEDITOR_OT_rename_replace,

    CYACOLLECTIONEDITOR_OT_apply_collection,
    CYAOBJECTLIST_OT_check_item,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.cyacollectioneditor_oa = PointerProperty(type=CYACOLLECTIONEDITOR_Props_OA)
    bpy.types.WindowManager.cyacollectioneditor_list = PointerProperty(type=CYACOLLECTIONEDITOR_Props_list)

    #bpy.app.handlers.depsgraph_update_post.append(cyacollectioneditor_handler)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.cyacollectioneditor_oa
    del bpy.types.WindowManager.cyacollectioneditor_list
    #bpy.utils.unregister_class(CYACOLLECTIONEDITOR_Props_item)

    #bpy.app.handlers.depsgraph_update_post.remove(cyacollectioneditor_handler)

