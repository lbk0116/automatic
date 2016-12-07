/**
 * Created by nantian on 2016/12/7.
 */
openerp.automatic=function(instance){
    var _t=instance.web._t,
        _lt=instance.web._lt,
        QWeb=instance.web.qweb;
    instance.automatic={};

    instance.automatic.Widget=instance.web.Widget.extend({
        activeMenu:"",
        init:function(){
            this.activeMenu=".oe_secondary_menus_container li.active>a>span";
        },
        start:function(o){
            var displayName=o.client.action_manager.inner_action.display_name;
            if(displayName=="Order"||displayName=="工单"){
                this.addBtn();
            }
        },
        addBtn:function(){
            var me=this;
            var timer=setInterval(function(){
                if($(me.activeMenu).length){
                    clearInterval(timer);
                    if($(me.activeMenu).html().trim()=="工单列表"){
                        a();
                    }
                }
            },100);
            function a(){
                var btn=$('<button type="button" class="importExcel">导入EXCEL</button>');
                $('.oe_list_buttons').append(btn);
                btn.click(function(){
                    me.popBox();
                });
            }
        },
        popBox:function(){
            var $form = $(QWeb.render("importExcel", {}));
            var $dialog=new instance.web.Dialog(null,{
                size: 'medium',
                dialogClass: 'oe_act_window',
                title: _t("导入Excel数据")
            },$form).open();
        }
    });
    //当视图加载时调用自己指定代码
    instance.web.actionList.push(new instance.automatic.Widget());
}