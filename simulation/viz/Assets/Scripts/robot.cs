using System.Collections.Generic;
using UnityEngine;

public class robot : MonoBehaviour
{
    public List<GameObject> items = new();

    public mainScript MainScript;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    public void setReference(mainScript mainscript) 
    { 
        MainScript = mainscript;
    }

    public void setRobotPosition(int x, int y) 
    {
        this.transform.position = new Vector3(x + 0.5f, 0.5f, y + 0.5f);
        foreach (var item in items) 
        {
            item.transform.position = new Vector3(x + 0.75f, item.transform.position.y, y + 0.75f);
        }
    }

    public void addToInventory(string itemName) 
    {
        Vector3 originalScale = MainScript.itemObjects[itemName].transform.localScale;

        GameObject itemClone = Instantiate(MainScript.itemObjects[itemName], 
            new Vector3(this.transform.position.x, 2.0f + (items.Count * 0.2f), this.transform.position.z), 
            this.transform.rotation);

        float carryFactor = 0.5f; 
        itemClone.transform.localScale = originalScale * carryFactor;
        itemClone.transform.parent = this.transform;

        items.Add(itemClone);
    }

    public void removeFromInventory(string itemName) 
    {
        items.RemoveAt(items.Count - 1);
    }


    public void clearInventory() 
    {
        foreach (var item in items) 
        {
            GameObject.Destroy(item);
        }
        items.Clear();
    }

}
