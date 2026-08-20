-- Inventory System
local InventorySystem = { Properties = { MaxSlots = { default = 20 } } }
function InventorySystem:OnActivate()
    self.items = {}
    self.count = 0
end
function InventorySystem:OnDeactivate() end
function InventorySystem:AddItem(item)
    if self.count >= self.Properties.MaxSlots then return false end
    table.insert(self.items, item)
    self.count = self.count + 1
    return true
end
function InventorySystem:RemoveItem(id)
    for i, item in ipairs(self.items) do
        if item.id == id then table.remove(self.items, i); self.count = self.count - 1; return true end
    end
    return false
end
function InventorySystem:HasItem(id)
    for _, item in ipairs(self.items) do
        if item.id == id then return true end
    end
    return false
end
function InventorySystem:GetItems() return self.items end
