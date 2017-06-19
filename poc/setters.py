class ClassWithSetter(object):
    @property
    def prop(self):
        return True

    @prop.setter
    def prop(self, value):
        print "setting prop in ClassWithSetter to %s" % value

class SubClassWithSetter(ClassWithSetter):
    @ClassWithSetter.prop.getter
    def prop(self):
        return False

    @ClassWithSetter.prop.setter
    def prop(self, value):
        print "setting prop in SubClass to %s" % value

c_ws = ClassWithSetter()
print "getting c_ws.prop: %s" % c_ws.prop
print "setting c_ws.prop"
c_ws.prop = False
sc_ws = SubClassWithSetter()
print "getting sc_ws.prop: %s" % sc_ws.prop
print "setting sc_ws.prop"
sc_ws.prop = True

class ClassNoSetter(object):
    @property
    def prop(self):
        return True

class SubClassNoSetter(ClassNoSetter):
    @ClassNoSetter.prop.getter
    def prop(self):
        return False

c_ns = ClassWithSetter()
print "getting c_ns.prop: %s" % c_ns.prop
print "setting c_ns.prop"
c_ns.prop = False
sc_ns = SubClassNoSetter()
print "getting sc_ns.prop: %s" % sc_ns.prop
print "setting sc_ns.prop"
sc_ns.prop = True
