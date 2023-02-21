using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;
using Peaksimple;

namespace PeaksimpleClient
{
    public partial class Form1 : Form
    {
        //  reference to connector
        private PeaksimpleConnector Connector;

        //  default channel number, 1-based
        private int Channel = 1;

        //  default control filename
        private string ControlFileName = "Vial1.CON";

        //  constructor
        public Form1()
        {
            InitializeComponent();

            //  create connector
            Connector = new PeaksimpleConnector();

            //  set default and display time out value
            textBoxTimeOut.Text = "10.0";
            textBoxChannel.Text = Channel.ToString();
        }

        //  Connect
        private void buttonConnect_Click(object sender, EventArgs e)
        {
            try
            {
                //  connect
                Connector.Connect();
                labelConnect.Text = "Success";
            }
            catch (Exception ex)
            {
                labelConnect.Text = "Could not connect - " + ex.GetType().ToString();
            }
        }

        //  Test call
        private void buttonTest_Click(object sender, EventArgs e)
        {
            try
            {
                //  test connection
                bool success = Connector.TestCall();
                labelSend.Text = "Returned " + success.ToString();
            }
            catch (Exception ex)
            {
                labelSend.Text = "Failed - " + ex.GetType().ToString();
            }
        }

        //  closed event
        private void Form1_FormClosed(object sender, FormClosedEventArgs e)
        {
            //  disconnect from Peaksimple
            Connector.Disconnect();
        }

        //  is data available?
        private void buttonIsDataAvailable_Click(object sender, EventArgs e)
        {
            try
            {
                //  returns how many data points are available since last read
                int dataAvailable = Connector.IsDataAvailable(Channel);
                labelIsDataAvailable.Text = "Available data = " + dataAvailable.ToString();
            }
            catch (Exception ex)
            {
                labelIsDataAvailable.Text = "Failed - " + ex.GetType().ToString();
            }
        }

        //  read data
        private void buttonReadData_Click(object sender, EventArgs e)
        {
            try
            {
                //  create array to store values
                Int32[] values;

                //  read values into array, and return the number of values read
                int valuesRead = Connector.ReadData(Channel, out values);
                labelReadData.Text = "Values read = " + valuesRead.ToString();
            }
            catch (Exception ex)
            {
                labelReadData.Text = "Failed = " + ex.GetType().ToString();
            }
        }

        //  are we currently in a run
        private void buttonIsRunning_Click(object sender, EventArgs e)
        {
            try
            {
                //  depends on channel
                bool isRunning = Connector.IsRunning(Channel);
                labelGetRunning.Text = "Running status = " + isRunning.ToString();
            }
            catch (Exception ex)
            {
                labelGetRunning.Text = "Failed - " + ex.GetType().ToString();
            }
        }

        //  start a run
        private void buttonStart_Click(object sender, EventArgs e)
        {
            try
            {
                //  call with parameter=true to start run
                Connector.SetRunning(Channel, true);
                labelSetRunning.Text = "Done";

                //  start a timer, so we can periodically read the data
                System.Windows.Forms.Timer acquisitionTimer = new System.Windows.Forms.Timer();
                acquisitionTimer.Interval = 500;  //  ms
                acquisitionTimer.Tick += new EventHandler(OnTimer);
                acquisitionTimer.Start();
            }
            catch (Exception ex)
            {
                labelSetRunning.Text = "Failed - " + ex.GetType().ToString();
            }
        }

        //  timer method
        private void OnTimer(object source, EventArgs e)
        {
            //  create array to store values
            Int32[] values;

            //  read any new data values
            int valuesRead = Connector.ReadData(Channel, out values);

            //  display them in the text box
            foreach (Int32 value in values)
            {
                textBoxData.Text += value.ToString() + "\r\n";
            }
        }

        //  stop a run
        private void buttonStop_Click(object sender, EventArgs e)
        {
            try
            {
                //  call with parameter=false to stop run
                Connector.SetRunning(Channel, false);
                labelSetRunning.Text = "Done";
            }
            catch (Exception ex)
            {
                labelSetRunning.Text = "Failed - " + ex.GetType().ToString();
            }
        }

        //  load a control file
        private void buttonLoadControlFilename_Click(object sender, EventArgs e)
        {
            try
            {
                //  load the control file given, fully qualified
                int result = Connector.LoadControlFile(ControlFileName);
                labelLoadControlFile.Text = "Result is " + result.ToString();
            }
            catch (Exception ex)
            {
                labelLoadControlFile.Text = "Failed - " + ex.GetType().ToString();
            }
        }

        //  set time out value
        private void buttonSetTimeOut_Click(object sender, EventArgs e)
        {
            try
            {
                Connector.TimeOut = Convert.ToDouble(textBoxTimeOut.Text);
                textBoxTimeOut.Text = Connector.TimeOut.ToString("N1");
            }
            catch (Exception)
            {
            }
        }

        //  set channel number
        private void buttonSetChannel_Click(object sender, EventArgs e)
        {
            Channel = Convert.ToInt32(textBoxChannel.Text);
            if (Channel < 1) Channel = 1;
            if (Channel > 6) Channel = 6;
            textBoxChannel.Text = Channel.ToString();
        }

    }
}