-- O3DE Core Component
local CoreComponent = {
    Properties = {
        Enabled = { default = true },
    },
}

function CoreComponent:OnActivate()
    self.tickHandler = TickBus.Connect(self, 0)
    Debug.Log("CoreComponent activated")
end

function CoreComponent:OnDeactivate()
    self.tickHandler:Disconnect()
end

function CoreComponent:OnTick(dt, tp)
    if not self.Properties.Enabled then return end
end
