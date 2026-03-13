using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using JetBrains.Annotations;
using Unity.VisualScripting;
using UnityEngine;


public class mainScript : MonoBehaviour
{
    // Start is called once before the first execution of Update after the MonoBehaviour is created

    public GameObject robotOriginal;
    public GameObject robotContainer;

    public GameObject shelfOriginal;
    public GameObject shelfContainer;

    public GameObject goalOriginal;
    public GameObject goalContainer;

    public GameObject canvas;

    public Dictionary<string, GameObject> robotDict = new Dictionary<string, GameObject>();
    public Dictionary<string, GameObject> shelfDict = new Dictionary<string, GameObject>();
    public Dictionary<string, GameObject> goalDict = new Dictionary<string, GameObject>();

    public Dictionary<string, GameObject> itemObjects = new Dictionary<string, GameObject>();

    public List<string> items = new List<string>();

    public bool waitingForStart = true;

    private System.Random rand = new System.Random();

    private TMPro.TextMeshProUGUI bottomtext;

    private int itemDisplayCtr = 0;

    void Start()
    {
        bottomtext = GameObject.FindGameObjectWithTag("BottomText").GetComponent<TMPro.TextMeshProUGUI>();
    }

    public void CreateRobot(string name, int x, int y)
    {
        GameObject robotClone = Instantiate(robotOriginal, new Vector3(0.5f + x, 0.5f, 0.5f + y), robotOriginal.transform.rotation);
        robotClone.transform.parent = robotContainer.transform;
        robotClone.name = name;
        robotClone.GetComponent<robot>().setReference(this);
        Renderer rend = robotClone.GetComponent<Renderer>();
        Material mat = new Material(Shader.Find("Standard"));

        mat.color = GenerateRandomColor();
        rend.material = mat;

        robotDict[robotClone.name] = robotClone;
    }

    public void CreateItem(string name)
    {
        this.items.Add(name);
        string[] parts = name.Split('_'); 

        float width = 1.0f;
        float height = 1.0f;

        string size = parts[1];
        switch (size.ToLower())
        {
            case "small":
                width = 1.0f; 
                height = 1.0f;
                break;
            case "medium":
                width = 2.4f; 
                height = 1.2f;
                break;
            case "large":
                width = 3.0f; 
                height = 3.0f;
                break;
            default:
                Debug.LogWarning("Unknown size passed: " + size);
                return;
        }

        Debug.Log($"Creating {size} item");
        createPolygonObj(itemDisplayCtr, -2, name, width, height);
        itemDisplayCtr += (int)width;
    }

    public Color GenerateRandomColor()
    {
        int red = rand.Next(0, 255);
        int blue = rand.Next(0, 255);
        int green = rand.Next(0, 255);
        return new Color((float)red / 255, (float)blue / 255, (float)green / 255);
    }

    public void CreateShelf(string name, int x, int y, string itemName)
    {
        GameObject shelfClone = Instantiate(shelfOriginal, new Vector3(0.5f + x, 1.5f, 0.5f + y), shelfOriginal.transform.rotation);
        shelfClone.transform.parent = shelfContainer.transform;
        shelfClone.name = name;

        shelfDict[shelfClone.name] = shelfClone;

        GameObject originalItem = this.itemObjects[itemName];
        GameObject itemClone = Instantiate(this.itemObjects[itemName], new Vector3(0.5f + x, 2.0f, 0.5f +y), shelfOriginal.transform.rotation);
        float shelfScaleFactor = 0.5f;
        itemClone.transform.localScale = originalItem.transform.localScale * shelfScaleFactor;
    }

    public void CreateGoal(string name, int x, int y)
    {
        GameObject goalClone = Instantiate(goalOriginal, new Vector3(0.5f + x, 0.5f, 0.5f + y), goalOriginal.transform.rotation);
        goalClone.transform.parent = goalContainer.transform;
        goalClone.name = name;
        goalClone.GetComponent<goal>().setReference(this);
        goalDict[goalClone.name] = goalClone;
    }


    public void startVisualisation()
    {
        this.waitingForStart = false;
    }

    // Update is called once per frame
    void Update()
    {
        if (!this.waitingForStart)
        {
            string textstring = "Items: ";
            bottomtext.text = textstring;
        }
    }

    public void correctScreenPosition()
    {
        int counter = 250;
        float uiScaleFactor = 0.5f;
        foreach (GameObject g in this.itemObjects.Values)
        {
            Camera cam = Camera.main;

            Debug.Log($"camera z {cam.transform.position.y}");
            Vector3 p = cam.ScreenToWorldPoint(new Vector3(counter, 70, cam.transform.position.y));

            Vector3 currentScale = g.transform.localScale;
            g.transform.localScale = new Vector3(currentScale.x * uiScaleFactor, currentScale.y, currentScale.z * uiScaleFactor);
            g.transform.position = new Vector3(p.x, p.y, p.z);

            counter += 100;
        }
    }

    void CreatePolygonObj(int x, int y, string name, float w, float h)
    {
        GameObject newobj = GameObject.CreatePrimitive(PrimitiveType.Cube);
        newobj.name = "Item";

        newobj.GetComponent<Renderer>().material.color = GenerateRandomColor();

        newobj.transform.position = new Vector3(x, y, 0);
        newobj.transform.localScale = new Vector3(w, 0.3f,h);

        this.itemObjects.Add(name, newobj);
    }
}
