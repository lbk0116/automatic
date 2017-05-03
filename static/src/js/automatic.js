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
        init:function(p){
            this.activeMenu=".oe_secondary_menus_container li.active>a>span";
        },
        start:function(){
            this.addBtn();
        },
        addBtn:function(){
            var me=this;
            var timer=setInterval(function(){
                if($(me.activeMenu).length&&$('.oe_list_buttons').length){
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
            $form.find("form").ajaxForm({
                url:"/import_order",
                type:"POST",
                success:function(txt){
                    if(txt=="导入成功"){
                        $dialog.close();
                        $("ul.oe_secondary_submenu>li.active>a").trigger("click");
                    }else{
                        window.alert(txt);
                    }
                }
            });
            var $dialog=new instance.web.Dialog(null,{
                size: 'small',
                dialogClass: 'oe_act_window',
                title: _t("导入Excel工单数据")
            },$form).open();
        }
    });

    instance.web.View.include({
        start:function(){
            var self = this;
            if(this.model == "automatic.order"){
                var automatic = new instance.automatic.Widget(self);
                automatic.start();
            }
            return this._super.apply(this, arguments);
        }
    });
}