using System.Collections.Generic;
using UnityEngine;

public class goal : MonoBehaviour 
{

    public List<GameObject> items = new();

    public mainScript MainScript;

    private float currentLayerY = 0f;
    private float nextSlotX = 0f;
    private float nextSlotZ = 0f;
    private float maxRowZ = 0f;
    private float maxLayerY = 0f;
    private float layerGap = 0.1f;

    public void addToInventory(string itemName)
    {
        // TODO this can be improved!! 
        string[] parts = itemName.Split('_');
        string size = parts[1].ToLower();
        float w = 0.8f, h = 0.8f;
        float extraOffset = 0.15f;

        if (size == "medium") { w = 1.8f; h = 0.8f; extraOffset = 0.1f;}
        else if (size == "large") { w = 2; h = 2; extraOffset = 0;}

        float carryFactor = 0.5f;
        float actualW = w * carryFactor;
        float actualZ = h * carryFactor;
        float actualThickness = 0.1f * carryFactor;
        float platformSize = 1.0f; 

        if (nextSlotX + actualW > platformSize + 0.01f)
        {
            nextSlotX = 0;
            nextSlotZ += maxRowZ;
            maxRowZ = 0; 
        }

        if (nextSlotZ + actualZ > platformSize + 0.01f)
        {
            nextSlotX = 0;
            nextSlotZ = 0;
            currentLayerY += maxLayerY + layerGap; 
            maxLayerY = 0; 
            maxRowZ = 0;
        }

        Vector3 spawnPos = new Vector3(
            this.transform.position.x - (platformSize / 2f) + nextSlotX + (actualW / 2f) + extraOffset,
            1.0f + currentLayerY + (actualThickness / 2f), 
            this.transform.position.z - (platformSize / 2f) + nextSlotZ + (actualZ / 2f) + extraOffset
        );

        GameObject itemClone = Instantiate(MainScript.itemObjects[itemName], spawnPos, this.transform.rotation);
        itemClone.transform.localScale = MainScript.itemObjects[itemName].transform.localScale * carryFactor;
        itemClone.transform.parent = this.transform;
        items.Add(itemClone);

        nextSlotX += actualW; 
        
        if (actualThickness > maxLayerY) maxLayerY = actualThickness;
        if (actualZ > maxRowZ) maxRowZ = actualZ;
    }

    public void removeFromInventory(string itemName)
    {
        items.RemoveAt(items.Count - 1);
    }

    public void setReference(mainScript mainscript)
    {
        MainScript = mainscript;
    }

    public void clearInventory()
    {
        foreach (var item in items)
        {
            GameObject.Destroy(item);
        }
        items.Clear();
        currentLayerY = 0f;
    }



}