namespace PeaksimpleClient
{
    partial class Form1
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.button1 = new System.Windows.Forms.Button();
            this.button2 = new System.Windows.Forms.Button();
            this.labelConnect = new System.Windows.Forms.Label();
            this.labelSend = new System.Windows.Forms.Label();
            this.buttonIsDataAvailable = new System.Windows.Forms.Button();
            this.labelIsDataAvailable = new System.Windows.Forms.Label();
            this.buttonReadData = new System.Windows.Forms.Button();
            this.labelReadData = new System.Windows.Forms.Label();
            this.textBoxData = new System.Windows.Forms.TextBox();
            this.buttonIsRunning = new System.Windows.Forms.Button();
            this.labelGetRunning = new System.Windows.Forms.Label();
            this.buttonStartRun = new System.Windows.Forms.Button();
            this.buttonStop = new System.Windows.Forms.Button();
            this.labelSetRunning = new System.Windows.Forms.Label();
            this.buttonLoadControlFile = new System.Windows.Forms.Button();
            this.labelLoadControlFile = new System.Windows.Forms.Label();
            this.label1 = new System.Windows.Forms.Label();
            this.textBoxTimeOut = new System.Windows.Forms.TextBox();
            this.buttonSetTimeOut = new System.Windows.Forms.Button();
            this.label2 = new System.Windows.Forms.Label();
            this.textBoxChannel = new System.Windows.Forms.TextBox();
            this.buttonChannel = new System.Windows.Forms.Button();
            this.SuspendLayout();
            // 
            // button1
            // 
            this.button1.Location = new System.Drawing.Point(28, 31);
            this.button1.Name = "button1";
            this.button1.Size = new System.Drawing.Size(275, 23);
            this.button1.TabIndex = 0;
            this.button1.Text = "Connect to local copy of Peakseimple, already running";
            this.button1.UseVisualStyleBackColor = true;
            this.button1.Click += new System.EventHandler(this.buttonConnect_Click);
            // 
            // button2
            // 
            this.button2.Location = new System.Drawing.Point(28, 76);
            this.button2.Name = "button2";
            this.button2.Size = new System.Drawing.Size(75, 23);
            this.button2.TabIndex = 0;
            this.button2.Text = "Test call";
            this.button2.UseVisualStyleBackColor = true;
            this.button2.Click += new System.EventHandler(this.buttonTest_Click);
            // 
            // labelConnect
            // 
            this.labelConnect.Location = new System.Drawing.Point(309, 36);
            this.labelConnect.Name = "labelConnect";
            this.labelConnect.Size = new System.Drawing.Size(307, 18);
            this.labelConnect.TabIndex = 1;
            // 
            // labelSend
            // 
            this.labelSend.Location = new System.Drawing.Point(194, 81);
            this.labelSend.Name = "labelSend";
            this.labelSend.Size = new System.Drawing.Size(393, 18);
            this.labelSend.TabIndex = 1;
            // 
            // buttonIsDataAvailable
            // 
            this.buttonIsDataAvailable.Location = new System.Drawing.Point(28, 119);
            this.buttonIsDataAvailable.Name = "buttonIsDataAvailable";
            this.buttonIsDataAvailable.Size = new System.Drawing.Size(96, 23);
            this.buttonIsDataAvailable.TabIndex = 0;
            this.buttonIsDataAvailable.Text = "IsDataAvailable";
            this.buttonIsDataAvailable.UseVisualStyleBackColor = true;
            this.buttonIsDataAvailable.Click += new System.EventHandler(this.buttonIsDataAvailable_Click);
            // 
            // labelIsDataAvailable
            // 
            this.labelIsDataAvailable.Location = new System.Drawing.Point(194, 124);
            this.labelIsDataAvailable.Name = "labelIsDataAvailable";
            this.labelIsDataAvailable.Size = new System.Drawing.Size(393, 18);
            this.labelIsDataAvailable.TabIndex = 1;
            // 
            // buttonReadData
            // 
            this.buttonReadData.Location = new System.Drawing.Point(28, 161);
            this.buttonReadData.Name = "buttonReadData";
            this.buttonReadData.Size = new System.Drawing.Size(96, 23);
            this.buttonReadData.TabIndex = 0;
            this.buttonReadData.Text = "ReadData";
            this.buttonReadData.UseVisualStyleBackColor = true;
            this.buttonReadData.Click += new System.EventHandler(this.buttonReadData_Click);
            // 
            // labelReadData
            // 
            this.labelReadData.Location = new System.Drawing.Point(194, 166);
            this.labelReadData.Name = "labelReadData";
            this.labelReadData.Size = new System.Drawing.Size(393, 18);
            this.labelReadData.TabIndex = 1;
            // 
            // textBoxData
            // 
            this.textBoxData.Location = new System.Drawing.Point(622, 31);
            this.textBoxData.Multiline = true;
            this.textBoxData.Name = "textBoxData";
            this.textBoxData.ScrollBars = System.Windows.Forms.ScrollBars.Both;
            this.textBoxData.Size = new System.Drawing.Size(100, 367);
            this.textBoxData.TabIndex = 2;
            // 
            // buttonIsRunning
            // 
            this.buttonIsRunning.Location = new System.Drawing.Point(28, 203);
            this.buttonIsRunning.Name = "buttonIsRunning";
            this.buttonIsRunning.Size = new System.Drawing.Size(96, 23);
            this.buttonIsRunning.TabIndex = 0;
            this.buttonIsRunning.Text = "IsRunning";
            this.buttonIsRunning.UseVisualStyleBackColor = true;
            this.buttonIsRunning.Click += new System.EventHandler(this.buttonIsRunning_Click);
            // 
            // labelGetRunning
            // 
            this.labelGetRunning.Location = new System.Drawing.Point(194, 208);
            this.labelGetRunning.Name = "labelGetRunning";
            this.labelGetRunning.Size = new System.Drawing.Size(393, 18);
            this.labelGetRunning.TabIndex = 1;
            // 
            // buttonStartRun
            // 
            this.buttonStartRun.Location = new System.Drawing.Point(28, 242);
            this.buttonStartRun.Name = "buttonStartRun";
            this.buttonStartRun.Size = new System.Drawing.Size(135, 23);
            this.buttonStartRun.TabIndex = 0;
            this.buttonStartRun.Text = "Start run and collect data";
            this.buttonStartRun.UseVisualStyleBackColor = true;
            this.buttonStartRun.Click += new System.EventHandler(this.buttonStart_Click);
            // 
            // buttonStop
            // 
            this.buttonStop.Location = new System.Drawing.Point(169, 242);
            this.buttonStop.Name = "buttonStop";
            this.buttonStop.Size = new System.Drawing.Size(65, 23);
            this.buttonStop.TabIndex = 0;
            this.buttonStop.Text = "Stop run";
            this.buttonStop.UseVisualStyleBackColor = true;
            this.buttonStop.Click += new System.EventHandler(this.buttonStop_Click);
            // 
            // labelSetRunning
            // 
            this.labelSetRunning.Location = new System.Drawing.Point(261, 247);
            this.labelSetRunning.Name = "labelSetRunning";
            this.labelSetRunning.Size = new System.Drawing.Size(246, 18);
            this.labelSetRunning.TabIndex = 1;
            // 
            // buttonLoadControlFile
            // 
            this.buttonLoadControlFile.Location = new System.Drawing.Point(28, 281);
            this.buttonLoadControlFile.Name = "buttonLoadControlFile";
            this.buttonLoadControlFile.Size = new System.Drawing.Size(96, 23);
            this.buttonLoadControlFile.TabIndex = 0;
            this.buttonLoadControlFile.Text = "LoadControlFile";
            this.buttonLoadControlFile.UseVisualStyleBackColor = true;
            this.buttonLoadControlFile.Click += new System.EventHandler(this.buttonLoadControlFilename_Click);
            // 
            // labelLoadControlFile
            // 
            this.labelLoadControlFile.Location = new System.Drawing.Point(194, 286);
            this.labelLoadControlFile.Name = "labelLoadControlFile";
            this.labelLoadControlFile.Size = new System.Drawing.Size(393, 18);
            this.labelLoadControlFile.TabIndex = 1;
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(28, 358);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(129, 13);
            this.label1.TabIndex = 3;
            this.label1.Text = "Time out value (seconds):";
            // 
            // textBoxTimeOut
            // 
            this.textBoxTimeOut.Location = new System.Drawing.Point(164, 355);
            this.textBoxTimeOut.Name = "textBoxTimeOut";
            this.textBoxTimeOut.Size = new System.Drawing.Size(43, 20);
            this.textBoxTimeOut.TabIndex = 4;
            // 
            // buttonSetTimeOut
            // 
            this.buttonSetTimeOut.Location = new System.Drawing.Point(218, 354);
            this.buttonSetTimeOut.Name = "buttonSetTimeOut";
            this.buttonSetTimeOut.Size = new System.Drawing.Size(60, 23);
            this.buttonSetTimeOut.TabIndex = 5;
            this.buttonSetTimeOut.Text = "Set";
            this.buttonSetTimeOut.UseVisualStyleBackColor = true;
            this.buttonSetTimeOut.Click += new System.EventHandler(this.buttonSetTimeOut_Click);
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(28, 322);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(111, 13);
            this.label2.TabIndex = 3;
            this.label2.Text = "Channel number (1-6):";
            // 
            // textBoxChannel
            // 
            this.textBoxChannel.Location = new System.Drawing.Point(164, 319);
            this.textBoxChannel.Name = "textBoxChannel";
            this.textBoxChannel.Size = new System.Drawing.Size(43, 20);
            this.textBoxChannel.TabIndex = 4;
            // 
            // buttonChannel
            // 
            this.buttonChannel.Location = new System.Drawing.Point(218, 318);
            this.buttonChannel.Name = "buttonChannel";
            this.buttonChannel.Size = new System.Drawing.Size(60, 23);
            this.buttonChannel.TabIndex = 5;
            this.buttonChannel.Text = "Set";
            this.buttonChannel.UseVisualStyleBackColor = true;
            this.buttonChannel.Click += new System.EventHandler(this.buttonSetChannel_Click);
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(774, 451);
            this.Controls.Add(this.buttonChannel);
            this.Controls.Add(this.buttonSetTimeOut);
            this.Controls.Add(this.textBoxChannel);
            this.Controls.Add(this.textBoxTimeOut);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.textBoxData);
            this.Controls.Add(this.labelLoadControlFile);
            this.Controls.Add(this.labelSetRunning);
            this.Controls.Add(this.labelGetRunning);
            this.Controls.Add(this.labelReadData);
            this.Controls.Add(this.labelIsDataAvailable);
            this.Controls.Add(this.labelSend);
            this.Controls.Add(this.buttonStop);
            this.Controls.Add(this.buttonStartRun);
            this.Controls.Add(this.buttonLoadControlFile);
            this.Controls.Add(this.buttonIsRunning);
            this.Controls.Add(this.buttonReadData);
            this.Controls.Add(this.buttonIsDataAvailable);
            this.Controls.Add(this.labelConnect);
            this.Controls.Add(this.button2);
            this.Controls.Add(this.button1);
            this.Name = "Form1";
            this.Text = "PeaksimpleConnector test harness";
            this.FormClosed += new System.Windows.Forms.FormClosedEventHandler(this.Form1_FormClosed);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Button button1;
        private System.Windows.Forms.Button button2;
        private System.Windows.Forms.Label labelConnect;
        private System.Windows.Forms.Label labelSend;
        private System.Windows.Forms.Button buttonIsDataAvailable;
        private System.Windows.Forms.Label labelIsDataAvailable;
        private System.Windows.Forms.Button buttonReadData;
        private System.Windows.Forms.Label labelReadData;
        private System.Windows.Forms.TextBox textBoxData;
        private System.Windows.Forms.Button buttonIsRunning;
        private System.Windows.Forms.Label labelGetRunning;
        private System.Windows.Forms.Button buttonStartRun;
        private System.Windows.Forms.Button buttonStop;
        private System.Windows.Forms.Label labelSetRunning;
        private System.Windows.Forms.Button buttonLoadControlFile;
        private System.Windows.Forms.Label labelLoadControlFile;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.TextBox textBoxTimeOut;
        private System.Windows.Forms.Button buttonSetTimeOut;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.TextBox textBoxChannel;
        private System.Windows.Forms.Button buttonChannel;
    }
}

