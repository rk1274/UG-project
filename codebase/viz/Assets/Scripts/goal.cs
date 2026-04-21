using System.Collections.Generic;
using UnityEngine;

public class goal : MonoBehaviour 
{
    public List<GameObject> items = new();

    public mainScript MainScript;

    // The grid represents the 4 slots on the goal and their current state.
    private Slot[] grid = new Slot[4] { new(), new(), new(), new() };

    // addToInventory adds an item to the goal's inventory and updates the visualisation accordingly.
    public void addToInventory(string itemName)
    {
        // These offsets are needed to position the item correctly on the goal.
        float zOffset = 0, xOffset = 0;
        int layer = 0;

        string size = itemName.Split('_')[1].ToLower();

        switch (size)
        {
            case "large":
                // Large will fill all slots and increase the layer if it isn't the first item.
                for (int i = 0; i < 4; i++) grid[i].Size = "L";

                if (grid[0].Size != "E")
                {
                    for (int i = 0; i < 4; i++) grid[i].Layer++;
                }

                layer = grid[0].Layer;

                break;

            case "medium":
                int startingSlotIdx = findBestSlotForMedium();

                layer = grid[startingSlotIdx].Layer;

                zOffset = (startingSlotIdx == 2) ? 0.3f : 0;
                zOffset -= 0.15f;

                break;

            case "small":
                int slotIdx = findBestSlotForSmall();

                zOffset = (slotIdx >= 2) ? 0.3f : 0;
                xOffset = (slotIdx % 2 != 0) ? 0.3f : 0;

                zOffset -= 0.15f;
                xOffset -= 0.15f;

                layer = grid[slotIdx].Layer;

                break;
        }

        float carryFactor = 0.5f;

        Vector3 pos = new Vector3(
            this.transform.position.x +xOffset, 
            1.0f + (layer * 0.1f), 
            this.transform.position.z +zOffset);

        GameObject itemClone = Instantiate(MainScript.itemObjects[itemName], pos, this.transform.rotation);
        itemClone.transform.localScale = MainScript.itemObjects[itemName].transform.localScale * carryFactor;
        itemClone.transform.parent = this.transform;
        items.Add(itemClone);
    }

    // findBestSlotForMedium finds the lowest suitable slot for a medium item
    // and returns the starting index of that slot (0 or 2).
    public int findBestSlotForMedium()
    {
        List<int> startIndexes = new();
        if (grid[0].Size == grid[1].Size)
        {
            startIndexes.Add(0);
        }

        if (grid[2].Size == grid[3].Size)
        {
            startIndexes.Add(2);
        }

        int idealStartIndex = 0;
        if (startIndexes.Count == 1)
        {
            idealStartIndex = startIndexes[0];
        } else if (grid[0].Layer > grid[2].Layer)
        {
            idealStartIndex = 2;
        }
        
        if (grid[idealStartIndex].Size != "E")
        {
            grid[idealStartIndex].Layer += 1;
            grid[idealStartIndex + 1].Layer += 1;
        }

        grid[idealStartIndex].Size = "M";
        grid[idealStartIndex + 1].Size = "M";

        return idealStartIndex;
    }

    // findBestSlotForSmall finds the lowest suitable slot for a small item 
    // and returns the index of the slot.
    public int findBestSlotForSmall()
    {
        int smallestIdx = 0;
        for (int i = 1; i < grid.Length; i++)
        {
            if (grid[i].Layer < grid[smallestIdx].Layer) smallestIdx = i;
        }

        if (grid[smallestIdx].Size != "E") grid[smallestIdx].Layer++;

        grid[smallestIdx].Size = "S";

        return smallestIdx;
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
        grid = new Slot[4] { new(), new(), new(), new() };
    }
}