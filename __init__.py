import bpy
from bpy.app.handlers import persistent
import imp

from bpy.types import(
    PropertyGroup,
    Operator,
    UIList,
    )

from bpy.props import(
    PointerProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    CollectionProperty,
    EnumProperty
    )

from .. import utils
from . import cmd

imp.reload(utils)
imp.reload(cmd)

bl_info = {
"name": "cya collection editor",
"author": "Takehito Tsuchiya",
"version": (0, 1),
"blender": (2, 93, 0),
"description": "cyacollectioneditor",
"category": "Object"}

try:
    bpy.utils.unregister_class(CYACOLLECTIONEDITOR_Props_item)
except:
    pass

#リストでアイテムを選択したときオブジェクトを選択する
@persistent
def cyaobjectlist_handler(scene):
    ui_list = bpy.context.window_manager.cyaobjectlist_list
    itemlist = ui_list.itemlist
    props = bpy.context.scene.cyaobjectlist_props

    #インデックスが変わったときだけ選択
    if len(itemlist) > 0:
        index = ui_list.active_index
        if props.currentindex != index:
            props.currentindex = index#先に実行しておかないとdeselectでhandlerがループしてしまう

            mode = utils.current_mode()
            if mode == 'OBJECT':
                bpy.ops.object.select_all(action='DESELECT')
                ob = utils.objectByName(itemlist[index].name)
                utils.act(ob)

            if mode == 'EDIT':
                bpy.ops.armature.select_all(action='DESELECT')
                utils.bone.selectByName(itemlist[index].name,True)

            if mode == 'POSE':
                utils.mode_e()
                bpy.ops.armature.select_all(action='DESELECT')
                utils.bone.selectByName(itemlist[index].name,True)
                utils.mode_p()


class CYACOLLECTIONEDITOR_Props_OA(PropertyGroup):
    currentindex : IntProperty()
    rename_string : StringProperty()
    replace_string : StringProperty()
    cloth_open : BoolProperty()
    setupik_lr : EnumProperty(items= (('l', 'l', 'L'),('r', 'r', 'R')))
    finger_step : IntProperty(default = 3 )
    chain_step : IntProperty(default = 0 )
    prefix_underbar : BoolProperty(default = True)

    suffix : EnumProperty(items= (('none', 'none', 'none'),('l', 'l', 'L'),('r', 'r', 'R'),('c', 'c', 'C')) )

#---------------------------------------------------------------------------------------
#リスト内のアイテムの見た目を指定
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_UL_uilist(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            #item.nameが表示される
            layout.prop(item, "bool_val", text = "")
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


#---------------------------------------------------------------------------------------
#リスト名 , list_id can be ””　，item_ptr ,item , index_pointer ,active_index
#active_indexをui_list.active_indexで取得できる
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_PT_ui(utils.panel):
    bl_label = "Object List"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout=self.layout
        row = layout.row()

        col = row.column()
        ui_list = context.window_manager.cyaobjectlist_list

        col.template_list("CYACOLLECTIONEDITOR_UL_uilist", "", ui_list, "itemlist", ui_list, "active_index", rows=8)
        col = row.column(align=True)

        col.operator("cyaobjectlist.select_all", icon='PROP_CON')
        col.operator("cyaobjectlist.add", icon=utils.icon['ADD'])
        col.operator("cyaobjectlist.remove", icon=utils.icon['REMOVE'])
        col.operator("cyaobjectlist.move_item", icon=utils.icon['UP']).dir = 'UP'
        col.operator("cyaobjectlist.move_item", icon=utils.icon['DOWN']).dir = 'DOWN'
        col.operator("cyaobjectlist.clear", icon=utils.icon['CANCEL'])
        col.operator("cyaobjectlist.remove_not_exist", icon='ERROR')

        row = layout.row(align=True)
        row.label( text = '' ,icon = 'CHECKMARK')

        array = (
        ('show','HIDE_OFF'),
        ('hide','HIDE_ON'),
        ('select','RESTRICT_SELECT_ON'),
        ('selected','DECORATE_LIBRARY_OVERRIDE'),
        ('invert','HOLDOUT_ON')
        )

        for x in array:
            row.operator("cyaobjectlist.check_item",icon = x[1] ).op = x[0]

        row.label( text = '' ,icon = 'TRASH')

        array = (
        ('checked','CHECKMARK'),
        ('unchecked','CHECKBOX_DEHLT'),
        )

        for x in array:
            row.operator("cyaobjectlist.remove_check_item", icon = x[1] ).op = x[0]


        # row = layout.row(align=True)
        # row.operator("cyaobjectlist.invert")

        row = layout.row(align=True)
        row.operator("cyaobjectlist.rename")#リネームのウインドウを表示
        row.operator("cyaobjectlist.bonetool")#リネームのウインドウを表示



#---------------------------------------------------------------------------------------
#リネームツール
#リネームとオブジェクト選択に関するツール群
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_MT_rename(Operator):
    bl_idname = "cyaobjectlist.rename"
    bl_label = "rename tool"

    def execute(self, context):
        return{'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self , width = 400 )

    def draw(self, context):
        props = bpy.context.scene.cyaobjectlist_props
        layout=self.layout

        row = layout.row()
        col = row.column()
        box = col.box()
        box.prop(props, "rename_string" , text = 'word')
        box.prop(props, "replace_string", text = 'replace')

        row1 = box.row()
        row1.operator("cyaobjectlist.rename_add_sequential_number" , icon = 'LINENUMBERS_ON')
        row1.operator("cyaobjectlist.rename_add_word" , text = 'add prefix').mode = 'prefix'
        row1.operator("cyaobjectlist.rename_add_word" , text = 'add suffix').mode = 'suffix'
        row1.prop(props, "prefix_underbar" , text = '_')


        row2 = box.row()
        for mode in ( 'replace' , 'l>r' , 'r>l' , 'del.number'):
            row2.operator("cyaobjectlist.rename_replace" , text = mode ).mode = mode



        box1 = box.box()
        row1 = box1.row()
        box1.prop(props, "suffix")
        row1.operator("cyaobjectlist.rename_add_word" , text = 'add suffix').mode = 'suffix_list'


        box.operator("cyaobjectlist.rename_bonecluster")
        box.operator("cyaobjectlist.rename_add_sequential_number" , icon = 'LINENUMBERS_ON')


        box = col.box()
        box.label(text = 'reneme finger')
        row0 = box.row()
        row0.operator("cyaobjectlist.rename_finger" , text = 'hand').mode = 0
        row0.operator("cyaobjectlist.rename_finger" , text = 'foot').mode = 1
        row0.prop(props, "finger_step")

        box = row.box()
        box.label(text = 'for UE4')
        for p in ('clavile_hand' ,'arm_twist' , 'thigh_toe' ,'leg_twist', 'pelvis_spine' , 'neck_head' , 'finger'):
            box.operator("cyaobjectlist.rename_bonechain_ue4" , text = p).pt = p
        box.prop(props, "setupik_lr", expand=True)



#---------------------------------------------------------------------------------------
#ボーンツール
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_MT_bonetool(Operator):
    bl_idname = "cyaobjectlist.bonetool"
    bl_label = "bone tool"

    def execute(self, context):
        return{'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self , width = 400 )

    def draw(self, context):
        props = bpy.context.scene.cyaobjectlist_props
        layout=self.layout

        row = layout.row()
        box = row.box()
        box.label(text = 'Cloth')
        box.operator("cyaobjectlist.create_mesh_from_bone")
        box.prop(props,"cloth_open")

        box = row.box()
        box.label(text = 'parent')
        box.operator("cyaobjectlist.parent_chain")
        box.prop(props, "chain_step")


#---------------------------------------------------------------------------------------
#リストのアイテムに他の情報を埋め込みたい場合はプロパティを追加できるのでいろいろ追加してみよう。
#ここでレジストしないと不具合がでる。register()に含めたいところだが。
#TestCollectionPropertyのitemListの型として指定する必要があるので後でレジストできない
#---------------------------------------------------------------------------------------

class CYACOLLECTIONEDITOR_Props_item(PropertyGroup):
    name : StringProperty(get=cmd.get_item, set=cmd.set_item)
    bool_val : BoolProperty( update = cmd.showhide )

bpy.utils.register_class(CYACOLLECTIONEDITOR_Props_item)


#---------------------------------------------------------------------------------------
#アイテムのリストクラス
#複数のアイテムをリストに持ち、リストにアイテムを加えたり、選択したリストを取得したりする。
#このクラス自体はuiをもっているわけではないので、現在リストで選択されているインデックスを取得する必要がある。
#
#col.template_list("Modifierlist_group_list", "", ui_list, "itemlist", ui_list, "active_index", rows=3)
#template_listで選択されたアイテムのインデックスをactive_indexに渡すため、上のように指定する必要がある。

#CollectionPropertyへの追加方法例
# item = self.list.add()
# item.name = bone.name
# item.int_val = 10
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_Props_list(PropertyGroup):
    active_index : IntProperty()
    itemlist : CollectionProperty(type=CYACOLLECTIONEDITOR_Props_item)#アイテムプロパティの型を収めることができるリストを生成

class CYACOLLECTIONEDITOR_OT_select_all(Operator):
    """全選択"""
    bl_idname = "cyaobjectlist.select_all"
    bl_label = ""
    def execute(self, context):
        cmd.select_all()
        return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_add(Operator):
    """選択を追加"""
    bl_idname = "cyaobjectlist.add"
    bl_label = ""
    def execute(self, context):
        cmd.add()
        return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_remove(Operator):
    """選択を削除"""
    bl_idname = "cyaobjectlist.remove"
    bl_label = ""

    def execute(self, context):
        cmd.remove()
        return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_remove_not_exist(Operator):
    """存在していないものを削除"""
    bl_idname = "cyaobjectlist.remove_not_exist"
    bl_label = ""
    def execute(self, context):
        cmd.remove_not_exist()
        return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_move_item(Operator):
    """アイテムの移動"""
    bl_idname = "cyaobjectlist.move_item"
    bl_label = ""
    dir : StringProperty(default='UP')

    def execute(self, context):
        cmd.move(self.dir)
        return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_clear(Operator):
    """アイテムのクリア"""
    bl_idname = "cyaobjectlist.clear"
    bl_label = ""
    def execute(self, context):
        cmd.clear()
        return {'FINISHED'}


class CYACOLLECTIONEDITOR_OT_check_item(Operator):
    """チェックされたアイテムの操作
1:表示　2:非表示　3:選択　4:選択中のものにチェック　5:反転"""
    bl_idname = "cyaobjectlist.check_item"
    bl_label = ""
    op : StringProperty()
    def execute(self, context):
        cmd.check_item(self.op)
        return {'FINISHED'}

# class CYACOLLECTIONEDITOR_OT_invert(Operator):
#     """チェックアイテムの並び順反転"""
#     bl_idname = "cyaobjectlist.invert"
#     bl_label = "invert"
#     def execute(self, context):
#         cmd.invert()
#         return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_remove_check_item(Operator):
    """リストから削除
1:チェックされたアイテム
2:チェックされていないアイテム"""
    bl_idname = "cyaobjectlist.remove_check_item"
    bl_label = ""
    op : StringProperty()
    def execute(self, context):
        cmd.remove_check_item(self.op)
        return {'FINISHED'}


#---------------------------------------------------------------------------------------
#rename tools
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_OT_rename_bonecluster(Operator):
    """First, add some top bones of cluster into objectlist."""
    bl_idname = "cyaobjectlist.rename_bonecluster"
    bl_label = "rename bone cluster"
    def execute(self, context):
        cmd.rename_bonecluster()
        return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_rename_replace(Operator):
    """First, add some top bones of cluster into objectlist."""
    bl_idname = "cyaobjectlist.rename_replace"
    bl_label = "replace"
    mode : StringProperty()
    def execute(self, context):
        cmd.rename_replace(self.mode)
        return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_rename_add_word(Operator):
    """First, add some top bones of cluster into objectlist."""
    bl_idname = "cyaobjectlist.rename_add_word"
    bl_label = ""
    mode : StringProperty()
    def execute(self, context):
        cmd.rename_add_word(self.mode)
        return {'FINISHED'}


#rename bones chain for UE4
class CYACOLLECTIONEDITOR_OT_rename_bonechain_ue4(Operator):
    """Arm : Add 4bones from clavile to hand in the list\nLeg : Add 4bones from thigh to toe in the list\nSpine and pelvis : Add from pelvis to spine\nFinger : Add each finger root bone. Sort from thumb to pinky."""
    bl_idname = "cyaobjectlist.rename_bonechain_ue4"
    bl_label = ""
    pt : StringProperty()

    def execute(self, context):
        cmd.bonechain_ue4(self.pt)
        return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_rename_finger(Operator):
    """First, add all finger bone roots from thumb to pinky , and set finger step finger chain number."""
    bl_idname = "cyaobjectlist.rename_finger"
    bl_label = ""
    mode : IntProperty()
    def execute(self, context):
        cmd.rename_finger(self.mode)
        return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_rename_add_sequential_renumber(Operator):
    """Rename some bones in list to add number."""
    bl_idname = "cyaobjectlist.rename_add_sequential_number"
    bl_label = ""
    def execute(self, context):
        cmd.rename_add_sequential_number()
        return {'FINISHED'}


#---------------------------------------------------------------------------------------
#ボーンツール
#---------------------------------------------------------------------------------------
class CYACOLLECTIONEDITOR_OT_create_mesh_from_bone(Operator):
    """選択ボーンからメッシュを作成する。ルートを選択して実行。名前でソートされる。"""
    bl_idname = "cyaobjectlist.create_mesh_from_bone"
    bl_label = "create mesh from bone"
    def execute(self, context):
        cmd.create_mesh_from_bone()
        return {'FINISHED'}

class CYACOLLECTIONEDITOR_OT_parent_chain(Operator):
    """Allow you to make a bone chain. First, add bones into list ordering from  end to root, and execute this command."""
    bl_idname = "cyaobjectlist.parent_chain"
    bl_label = "parent chain"
    def execute(self, context):
        cmd.parent_chain()
        return {'FINISHED'}



classes = (
    CYACOLLECTIONEDITOR_Props_OA,
    CYACOLLECTIONEDITOR_UL_uilist,
    CYACOLLECTIONEDITOR_PT_ui,
    CYACOLLECTIONEDITOR_Props_list,
    CYACOLLECTIONEDITOR_MT_rename,
    CYACOLLECTIONEDITOR_MT_bonetool,


    CYACOLLECTIONEDITOR_OT_select_all,
    CYACOLLECTIONEDITOR_OT_add,
    CYACOLLECTIONEDITOR_OT_remove,
    CYACOLLECTIONEDITOR_OT_remove_not_exist,
    CYACOLLECTIONEDITOR_OT_move_item,
    CYACOLLECTIONEDITOR_OT_clear,

    CYACOLLECTIONEDITOR_OT_check_item,
    #CYACOLLECTIONEDITOR_OT_invert,
    CYACOLLECTIONEDITOR_OT_remove_check_item,

    #rename
    CYACOLLECTIONEDITOR_OT_rename_bonecluster,
    CYACOLLECTIONEDITOR_OT_rename_bonechain_ue4,
    CYACOLLECTIONEDITOR_OT_rename_replace,

    CYACOLLECTIONEDITOR_OT_create_mesh_from_bone,
    CYACOLLECTIONEDITOR_OT_rename_finger,
    CYACOLLECTIONEDITOR_OT_rename_add_sequential_renumber,

    CYACOLLECTIONEDITOR_OT_rename_add_word,

    #bone
    CYACOLLECTIONEDITOR_OT_parent_chain

)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.cyaobjectlist_props = PointerProperty(type=CYACOLLECTIONEDITOR_Props_OA)
    bpy.types.WindowManager.cyaobjectlist_list = PointerProperty(type=CYACOLLECTIONEDITOR_Props_list)
    bpy.app.handlers.depsgraph_update_pre.append(cyaobjectlist_handler)



def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.cyaobjectlist_props
    del bpy.types.WindowManager.cyaobjectlist_list
    bpy.app.handlers.depsgraph_update_pre.remove(cyaobjectlist_handler)

