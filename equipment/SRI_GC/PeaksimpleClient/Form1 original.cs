using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;
using System.IO;
using System.IO.Pipes;
using System.Threading;

namespace PeaksimpleClient
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        //  the pipes
        static private NamedPipeClientStream Pipe = null;
        static private NamedPipeClientStream PipeRespond = null;

        //  current response message details
        static int ResponseMessageID = 0;
        static int ResponseParameterLength = 0;
        static byte[] ResponseBuffer = new byte[1024];

        //  connect
        private void button1_Click(object sender, EventArgs e)
        {
            //  create pipes
            Pipe = new NamedPipeClientStream(".", "PeaksimplePipe",PipeDirection.Out);

            //  connect the pipes
            try
            {
                //  connect
                Pipe.Connect(3000);

                //  start and connect to respond pipe on other thread
                labelConnect.Text = "OK";

                //  create response pipe
                PipeRespond = new NamedPipeClientStream(".", "PeaksimplePipeRespond", PipeDirection.In, PipeOptions.Asynchronous);

                //  connect response pipe
                PipeRespond.Connect(3000);

                //  start async read
                PipeRespond.BeginRead(ResponseBuffer, 0, 1024, new AsyncCallback(AsyncReceive), PipeRespond);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine("Could not connect pipe: " + ex.ToString());
                labelConnect.Text = "Fail";
            }
        }

        private static void AsyncReceive(IAsyncResult iar)
        {
            //  end read
            int bytes = PipeRespond.EndRead(iar);
            System.Diagnostics.Debug.WriteLine("Bytes read = " + bytes.ToString());

            //  get length byte
            int length = ResponseBuffer[0];
            if (bytes == length)
            {
                //  note message ID
                ResponseMessageID = ResponseBuffer[1];
            }

            //  start another
            PipeRespond.BeginRead(ResponseBuffer, 0, 1024, new AsyncCallback(AsyncReceive), PipeRespond);
        }

        private void button2_Click(object sender, EventArgs e)
        {
            //  check pipes are available and connected
            if (Pipe == null)
                return;
            if (!Pipe.IsConnected)
                return;

            //  create a message
            byte[] bytes={4,28,29,30};

            //  send the message
            try
            {
                //  clear response message ID
                ResponseMessageID = 0;

                //  send
                System.Diagnostics.Debug.WriteLine("Sending!");
                labelSend.Text = "Sent";
                Pipe.Write(bytes, 0, 4);
                Pipe.Flush();

#if true
                //  wait for response
                while (true)
                {
                    if (ResponseMessageID > 0)
                        break;
                }
                System.Diagnostics.Debug.WriteLine("Message received");
                ResponseParameterLength = ResponseBuffer[0] - 2;
                labelSend.Text = "Message=" + ResponseMessageID.ToString() + " [";
                for (int i = 0; i < ResponseParameterLength; ++i)
                    labelSend.Text += ResponseBuffer[i+2].ToString() + " ";
                labelSend.Text += "]";
#endif
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine("Could not send: " + ex.ToString());
                labelSend.Text = "Fail";
            }
        }

        private void Form1_FormClosed(object sender, FormClosedEventArgs e)
        {
        }
    }
}