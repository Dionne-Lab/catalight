Examples
=============
More Scripted Study Control Examples
------------------------------------
Please first look at the :ref:`basic scripting example <scripting>` in the introduction section for the main study level control functions to use in the scripting interface. Here we fully demonstrate application of the available experiment types and another helpful function.

.. code-block:: python
    :caption: This helpful function determines the approximate total time the current study will take to complete.

    def calculate_time(expt_list):
        start_time = time.time()
        run_time = []
        for expt in expt_list:
            run_time.append(expt.plot_sweep()[-1])
            print(run_time)
            if max(expt.power) > 0:
                laser_on = time.localtime(start_time + 60 * sum(run_time[:-1]))
                laser_off = time.localtime(start_time + 60 * sum(run_time))
                time_on = time.strftime('%b-%d at %I:%M%p', laser_on)
                time_off = time.strftime('%b-%d at %I:%M%p', laser_off)
                print('laser on from %s to %s' % (time_on, time_off))

        end_time = time.localtime(start_time + 60 * sum(run_time))
        end_time = time.strftime('%b-%d at %I:%M%p', end_time)
        print('experiment will end on %s' % (end_time))

.. code-block:: python
    :caption: prereduction, power and temperature sweeps

    expt1 = Experiment(eqpt_list)
    expt1.expt_type = 'temp_sweep'
    expt1.temp = list(np.arange(300, 401, 10))
    expt1.gas_type = ['C2H2', 'Ar', 'H2']
    expt1.gas_comp = [[0.01, 1-0.06, 0.05]]
    expt1.tot_flow = [50]
    expt1.sample_name = sample_name
    expt1.create_dirs(os.path.join(main_fol, 'prereduction'))

    expt2 = Experiment(eqpt_list)
    expt2.expt_type = 'power_sweep'
    expt2.temp = [300]
    expt2.power = list(np.arange(0, 301, 50))
    expt2.gas_type = ['C2H2', 'Ar', 'H2']
    expt2.gas_comp = [[0.01, 1-0.06, 0.05]]
    expt2.tot_flow = [50]
    expt2.sample_name = sample_name
    expt2.create_dirs(os.path.join(main_fol, 'prereduction'))

.. code-block:: python
    :caption: A reduction can be run by defining a stability test. The time for the stability test is determines by the sample_set_size attribute and the sample_rate attribute of the GC_Connector used. You can see that the independent variable labeled within the Experiment.expt_list attribute is temperature, but this can just be set as a single value for stability tests.

    reduction = Experiment(eqpt_list)
    # Use the sample set size to determine the length of the reduction
    # Here, the sample time is 12 minutes, and we run 10 collections
    # for a 2 hr reduction (this isn't accounting for
    # steady state, buffer, and ramp times
    reduction.sample_set_size = 10
    reduction.expt_type = 'stability_test'
    reduction.temp = [295]
    reduction.gas_type = ['C2H2', 'Ar', 'H2']
    reduction.gas_comp = [[0, 0, 1]]
    reduction.tot_flow = [50]
    reduction.sample_name = sample_name
    reduction.create_dirs(main_fol)

.. code-block:: python
    :caption: postreduction, power and temperature sweeps

    expt3 = Experiment(eqpt_list)
    expt3.expt_type = 'temp_sweep'
    expt3.temp = list(np.arange(300, 401, 10))
    expt3.gas_type = ['C2H2', 'Ar', 'H2']
    expt3.gas_comp = [[0.1, 1-0.6, 0.5]]
    expt3.tot_flow = [50]
    expt3.sample_name = sample_name
    expt3.create_dirs(os.path.join(main_fol, 'postreduction'))

    expt4 = Experiment(eqpt_list)
    expt4.expt_type = 'power_sweep'
    expt4.temp = [300]
    expt4.power = list(np.arange(0, 301, 50))
    expt4.gas_type = ['C2H2', 'Ar', 'H2']
    expt4.gas_comp = [[0.1, 1-0.6, 0.5]]
    expt4.tot_flow = [50]
    expt4.sample_name = sample_name
    expt4.create_dirs(os.path.join(main_fol, 'postreduction'))

.. code-block:: python
    :caption: Here are examples of the additional experiment types currently available.

    stability_test = Experiment(eqpt_list)
    stability_test.sample_set_size = 40
    stability_test.expt_type = 'stability_test'
    stability_test.temp = [373]
    stability_test.gas_type = ['C2H2', 'Ar', 'H2']
    stability_test.gas_comp = [[0.01, 1-0.06, 0.05]]
    stability_test.tot_flow = [50]
    stability_test.sample_name = sample_name
    stability_test.create_dirs(os.path.join(main_fol, 'postreduction'))

    expt5 = Experiment(eqpt_list)
    expt5.expt_type = 'flow_sweep'
    expt5.temp = [340]
    expt5.gas_type = ['C2H2', 'Ar', 'H2']
    expt5.gas_comp = [[0.01, 1-0.03, 0.02]]
    expt5.tot_flow = list(np.arange(10, 60, 10))
    expt5.sample_name = sample_name
    expt5.create_dirs(os.path.join(main_fol, 'postreduction'))

    expt6 = Experiment(eqpt_list)
    expt6.expt_type = 'comp_sweep'
    expt6.temp = [340]
    P_h2 = 0.01*np.array([0.5, 1, 2, 5, 10, 15, 20, 30, 40])
    P_c2h2 = 0.01*np.ones(len(P_h2))
    P_Ar = 1-P_c2h2-P_h2
    expt6.gas_comp = np.stack([P_c2h2, P_Ar, P_h2], axis=1).tolist()
    expt6.tot_flow = [50]
    expt6.sample_name = sample_name
    expt6.create_dirs(os.path.join(main_fol, 'postreduction'))

    expt_list = [expt1, expt2, reduction,
                 expt3, expt4, stability_test,
                 expt5, expt6]  # Order is important here!!
    calculate_time(expt_list)
    run_study(expt_list, eqpt_list)
    shut_down(eqpt_list)


Training Videos
===============
We have created a `youtube playlist <https://www.youtube.com/playlist?list=PLZdPKi6exYOAvwgxAP9JBAuJ5nciuvDhu>`_ with videos of some of the most important features of the catalight system:

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
       <iframe src="https://www.youtube.com/embed/-8Cob1xNpf4?list=PLZdPKi6exYOAvwgxAP9JBAuJ5nciuvDhu" title="Catalight: Introduction to the GUI" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>
    <br/>
    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/6VJg5W6GpIg?list=PLZdPKi6exYOAvwgxAP9JBAuJ5nciuvDhu" title="Catalight: Running a Calibration" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>
    <br/>
    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/M1izA4k8QBw?list=PLZdPKi6exYOAvwgxAP9JBAuJ5nciuvDhu" title="Catalight: Initial Data Analysis" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>
    <br/>
    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/urjR0mDqkzE?list=PLZdPKi6exYOAvwgxAP9JBAuJ5nciuvDhu" title="Catalight: Using the Multiplot Tool" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>
    <br/>
