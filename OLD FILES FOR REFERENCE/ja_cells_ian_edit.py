# %%
import os
import gdstk as gd
import numpy as np
from enum import Enum
from typing import Union


class IDT_Type(Enum):
    STANDARD = 'standard'
    EWC = 'EWC'
    DART = 'dart'
    SPLIT_FINGER = 'split'
    FOCUSED = 'focused'
    OPEN = 'open'


class Bar_Type(Enum):
    BAR = 'bar'
    DISC = 'disc'


def gsg_pad(lib, layers, layer, p=150, x=80, y=70, connect_grounds=False):
    c = lib.new_cell(f'GSG_pad_Layer{layer}_P{p}_x{x}_y{y}_tiedGnd{connect_grounds}')
    #  signal pad
    c.add(gd.rectangle((-x/2, -y/2), (x/2, y/2), layer=layers[layer]))
    # rt = gd.Polygon([(x/2, -y/2),(x/2+40, -y/2+10),(x/2+40, y/2-10),(x/2, y/2)])

    #  ground pads
    c.add(gd.rectangle((-x/2-20, -y/2-p), (x/2, y/2-p), layer=layers[layer]))
    c.add(gd.rectangle((-x/2-20, -y/2+p), (x/2, y/2+p), layer=layers[layer]))

    if connect_grounds:
        c.add(gd.rectangle((-x/2-40, -y/2-p), (-x/2-20, y/2+p), layer=layers[layer]))
    return c


def dc_pad(lib, layers, layer, x=80, y=70):
    c = lib.new_cell(f'dc_pad_Layer{layer}_x{x}_y{y}')
    #  signal pad
    c.add(gd.rectangle((-x/2, -y/2), (x/2, y/2), layer=layers[layer]))
    return c


def bar_resonator(lib, pads, layers, d=150, x=30, y=200, yoff=40, r=0, trench=False,
                  name=None, type=Bar_Type.BAR):
    """

    :param lib:
    :param pads: gdspy padset cell
    :param layers: list of mask layers in format [trench, metal1]
    :param d: distance between port 1 and 2 electrodes, inner edge to inner edge
    :param x: width of electrodes
    :param y: length of overlap between port 1 and 2 electrodes
    :param yoff: additional length of electrode before pad taper
    :param trench: bool, determines if resonator has a trench or not
    :return: c: bar resonator cell
    """
    if name == None:
        name = type.value+f'_res_d{d}_x{x}_y{y}'
    if type == Bar_Type.DISC:
        name = name+f'_r{r}'
    c = lib.new_cell(name)

    pad_extent = gd.Reference(pads).bounding_box()
    c.add(gd.Reference(pads,
                           rotation=np.pi/180*-90,
                           origin=(d/2+x/2, y/2+pad_extent[1][0]+30+yoff)))
    c.add(gd.Reference(pads,
                           rotation=np.pi/180*90,
                           origin=(-d/2-x/2, -y/2-pad_extent[1][0]-30-yoff)))

    c.add(gd.Polygon([(pad_extent[0][1]+d/2+x/2, y/2+yoff+30),
                      (pad_extent[0][1]+d/2+x/2+70, y/2+yoff+30),
                      (pad_extent[0][1]-d/2-x/2+70, -y/2-yoff-30),
                      (pad_extent[0][1]-d/2-x/2, -y/2-yoff-30),
                      ], layers['M1']), )
    c.add(gd.Polygon([(-pad_extent[0][1]+d/2+x/2, y/2+yoff+30),
                      (-pad_extent[0][1]+d/2+x/2-70, y/2+yoff+30),
                      (-pad_extent[0][1]-d/2-x/2-70, -y/2-yoff-30),
                      (-pad_extent[0][1]-d/2-x/2, -y/2-yoff-30),
                      ], layers['M1']), )

    # Pad Tapers
    c.add(gd.Polygon([(d/2, y/2+yoff),
                      (d/2+(x-70)/2, y/2+30+yoff),
                      (d/2+x-(x-70)/2, y/2+30+yoff),
                      (d/2+x, y/2+yoff)
                      ], layers['M1']), )
    c.add(gd.Polygon([(-d/2, -y/2-yoff),
                      (-d/2-(x-70)/2, -y/2-30-yoff),
                      (-d/2-x+(x-70)/2, -y/2-30-yoff),
                      (-d/2-x, -y/2-yoff)
                      ], layers['M1']), )
    if type == Bar_Type.DISC:
        disc_cut = gd.Round((0, 0), radius=r, layer=layers['M1'])
    else:
        disc_cut = gd.rectangle((0, 0), (0, 0), layer=layers['M1'])

    c.add(gd.boolean(gd.rectangle((-d/2-x, -y/2-yoff), (-d/2, y/2), layers['M1']),
                     disc_cut,
                     'not', layer=layers['M1']))
    c.add(gd.boolean(gd.rectangle((d/2, -y/2), (d/2+x, y/2+yoff), layers['M1']),
                     disc_cut,
                     'not', layer=layers['M1']))

    if trench and d > 10:
        c.add(
            gd.rectangle((-d/2+5, -y/2-yoff/2), (d/2-5, y/2+yoff/2), layers['Trench']))
    extent = c.bounding_box()
    for o in gd.text(name, 20, (extent[0][0], extent[1][1]+5), layer=layers['M1']):
        c.add(o)
    return c


def bar_resonator_matrix(lib, pads, layers, ds, xs, ys, rs, trench=False,
                         name='Resonator Matrix', **kwargs):
    m = lib.new_cell(name)
    max_x = 0
    max_y = 0
    cells = []
    x0 = []
    y0 = []

    # handles parsing of d,x,y,r to find two arrays to iterate over

    pd, p2, p1i, p2i = [None]*4
    p1 = np.empty(0)
    p2 = np.empty(0)

    ps = [None]*4
    for i, p in enumerate([ds, xs, ys, rs]):
        p = np.asarray(p)
        if p.size == 1:
            ps[i] = p
        elif (p1.size == 0):
            p1 = p
            p1i = i
        elif (p2.size == 0):
            p2 = p
            p2i = i
        else:
            raise ValueError("More than two series given.")

    for i, ps[p1i] in enumerate(p1):
        for j, ps[p2i] in enumerate(p2):
            c = bar_resonator(lib, pads, layers, d=ps[0], x=ps[1], y=ps[2], r=ps[3],
                              trench=trench, **kwargs)
            x0.append(i)
            y0.append(j)
            cells.append(c)
            extent = c.bounding_box()
            print(extent)
            if extent[1][0]-extent[0][0] > max_x:
                max_x = extent[1][0]-extent[0][0]
            else:
                pass
            if extent[1][1]-extent[0][1] > max_y:
                max_y = extent[1][1]-extent[0][1]
            else:
                pass
    x0 = (np.asarray(x0)*max_x*1.1)
    y0 = (np.asarray(y0)*max_y*1.1)
    for i, r in enumerate(cells):
        m.add(gd.Reference(r, origin=(x0[i], y0[i])))


def idt_device(lib: gd.Library, pads: gd.Cell, layers: dict, lmda: float,
               g_idt: float, idt_type: IDT_Type = IDT_Type.STANDARD,
               process_bias: float = 0, n_idt: int = 20, w_b: float = 5, s_b: float = 1,
               l_idt: float = None,
               reflector: bool = False, g_r: float = None, w_br: float = None,
               n_idtr: int = None, w_r: float = None,
               s_r: float = None, theta: float = None, connect_port_grounds=False,
               pad_rot: int = False, cell_prefix='') -> gd.Cell:
    """

    :param lib: gdspy library to add cells to
    :param pads: probe pad set to use
    :param layers: mask layer dictionary
    :param lmda: Desired wavelength. IDT dimensions set by this and idt_type
    :param g_idt: gap between two port IDT delay lines. Set to 0 for single port device.
    :param idt_type: specifies normal lmda/4 IDT, SPUDT type, or focused IDT
    :param process_bias: Standard IDTs only. Increases metal width & decreases space width to account for process bias.
    :param n_idt: number of IDT fingers in a block
    :param w_b: width of busbar
    :param s_b: spacing from end of idt to busbar (sets aperture with l_idt)
    :param l_idt: length of IDTs
    :param reflector: Toggles reflector on and off
    :param g_r: gap from edge of IDT block to reflector edge (lambda/4 different from center-to-center).
    Should be lambda*(n/2+1/8) for +pi/2 reflection phase, - reflection coef (niobate shorted refl),
      lambda*(n/2+3/8) for -pi/2 reflection phase, + refl. coef (niobate open refl)
    :param w_br: width reflector busbar
    :param n_idtr: number of reflector IDTs
    :param w_r: metal width of reflector IDTs
    :param s_r: space width of reflector IDTs
    :param theta: aperture angle for focused IDTs
    :param connect_port_grounds: toggle ground ring around device
    :param pad_rot: toggles 90 degree pad rotation for single port IDTs (g_idt=0)
        0 - standard pads
        1 - rotated pads with GS taper inline with IDT
        2 - rotated pads with GS taper at angle to IDTs
    :param cell_prefix: text to add to front of cell name
    :return: gdspy cell of IDT device
    """
    pad_tapery = 50  # offset distance for tapering from pad edge to IDT busbar
    v1_y = 10
    M2_OVERLAP = 1
    dev_x_extent = 0
    cell_name = cell_prefix

    # Parameter Setup, idt creation
    if l_idt is None:
        l_idt = 100*lmda
    if idt_type == IDT_Type.STANDARD:
        cell_name = cell_name+'dIDT'
        w_idt = lmda/4+process_bias
        s_idt = lmda/4-process_bias
        idts = idt_cell(lib, layers, w_idt, s_idt, l_idt, n_idt, w_b, s_b)
        bb_offset = s_idt
    elif idt_type == IDT_Type.EWC:
        if process_bias != 0:
            raise NotImplementedError("Process bias not implemented for SPUDT devices")
        cell_name = cell_name+'dEWC'
        idts = ewc_cell(lib, layers, lmda, process_bias, l_idt, n_idt, w_b, s_b)
        bb_offset = 3*lmda/16
    elif idt_type == IDT_Type.SPLIT_FINGER:
        cell_name = cell_name+'dSplitFing'
        idts = split_finger_cell(lib, layers, lmda, process_bias, l_idt, n_idt, w_b,
                                 s_b)
        bb_offset = lmda/8
    elif idt_type == IDT_Type.DART:
        if process_bias != 0:
            raise NotImplementedError("Process bias not implemented for SPUDT devices")
        cell_name = cell_name+'dDART'
        idts = dart_cell(lib, layers, lmda, process_bias, l_idt, n_idt, w_b, s_b)
        bb_offset = lmda/8
    elif idt_type == IDT_Type.FOCUSED:
        if theta is None:
            raise ValueError("No angle defined for focused IDT.")
        else:
            cell_name = cell_name+f'dFoc_thta{theta:.1f}'
            w_idt = lmda/4+process_bias
            s_idt = lmda/4-process_bias
            idts = focused_idt_cell(lib, layers, w_idt, s_idt, theta, g_idt, n_idt, w_b,
                                    s_b)
            bb_offset = s_idt
    elif idt_type == IDT_Type.OPEN:
        cell_name = cell_name+'OPEN'
        w_idt = lmda/4+process_bias
        s_idt = lmda/4-process_bias
        bb_offset = s_idt
        idts = idt_cell(lib, layers, w_idt, s_idt, l_idt, n_idt, w_b, s_b)

    text_label = cell_name+f'_lmbda{lmda:.3f}_g{g_idt:.1f}_nI{n_idt:.1f}_lI{l_idt:.1f}'
    cell_name = cell_name+f'_lambda{lmda:.3f}_g{g_idt:.1f}_nIDT{n_idt:.1f}_IDTl{l_idt:.1f}_wb{w_b:.1f}_sb{s_b:.1f}_bias{process_bias:.3f}'
    if reflector is True:
        if g_r is None: g_r = 3/8*lmda  # TODO: Change default value based on simulated performance
        if w_br is None: w_br = w_b
        if w_r is None: w_r = lmda/4+process_bias
        if s_r is None: s_r = lmda/4-process_bias
        if n_idtr is None: n_idtr = n_idt
        cell_name = cell_name+f'_gr{g_r:.1f}_wr{w_r:.1f}_sr{s_r:.1f}_wbr{w_br:.1f}_nR{n_idtr:.1f}'
        text_label = text_label+f'_gr{g_r:.1f}_nR{n_idtr:.1f}'

    # Cell Creation
    c = lib.new_cell(cell_name)
    idt_extent = idts.bounding_box()
    if idt_type == IDT_Type.FOCUSED:
        idt_offset = 0  # cell extent goes to focal point
    else:
        idt_offset = g_idt/2+idt_extent[1][0]

        if g_idt == 0:  # one-port IDT
            idt_offset = (idt_extent[1][0]+idt_extent[0][0])/2
            if idt_type == IDT_Type.OPEN:
                pass
            else:
                c.add(gd.Reference(idts, origin=(-idt_offset, 0), rotation=np.pi/180*0))
        else:
            if idt_type == IDT_Type.OPEN:
                pass
            else:
                c.add(gd.Reference(idts, origin=(-idt_offset, 0),
                                       rotation=np.pi/180*180))  # rotation puts idt finger at gap edge
                c.add(gd.Reference(idts, origin=(idt_offset, 0), rotation=np.pi/180*0))
    dev_x_extent = idt_offset+idt_extent[1][0]
    if reflector is True:
        if idt_type == IDT_Type.FOCUSED:
            r = focused_idt_reflector(lib, layers, w_r, s_r, theta,
                                      g_idt+2*(g_r+n_idt*lmda-lmda/4), n_idtr, w_br)
            r_extent = gd.Reference(r).bounding_box()
            r_offset = 0  # r_extent[0][0]
            dev_x_extent = r_extent[1][0]
        else:
            r = idt_reflector(lib, layers, w_r, s_r, l_idt, n_idtr, w_br)
            r_extent = gd.Reference(r).bounding_box()
            r_center = (r_extent[1][0]+r_extent[0][0])/2
            r_xoff = (r_extent[1][0]-r_extent[0][0])/2
            if g != 0:
               r_offset = g_idt/2+(idt_extent[1][0]-idt_extent[0][0])+r_extent[1][0]+g_r
            else:
                r_offset = idt_extent[1][0]-idt_offset+r_xoff-r_center+g_r
            dev_x_extent = dev_x_extent+r_extent[1][0]
        if idt_type != IDT_Type.OPEN:
            c.add(gd.Reference(r, origin=(r_offset, 0)))
            c.add(gd.Reference(r, origin=(-r_offset, 0), rotation=np.pi/180*180))

    # JOEL field rectangle to prevent stitching errors in IDT
    if idt_type != IDT_Type.OPEN:
        cell_idt_extents = c.bounding_box()
        if cell_idt_extents[1][1]-cell_idt_extents[1][0]+2*(w_b+v1_y) < 980 and \
                cell_idt_extents[0][1]-cell_idt_extents[0][0] < 980:
            c.add(gd.rectangle([cell_idt_extents[0][0]-5, cell_idt_extents[0][1]-5],
                               [cell_idt_extents[1][0]+5, cell_idt_extents[1][1]+5],
                               layers['JOEL_FIELD']))
        elif idt_extent[1][1]-idt_extent[1][0] < 980 and idt_extent[0][1]-idt_extent[0][
            0] < 980:
            c.add(gd.rectangle(
                [idt_extent[0][0]-5-idt_offset, idt_extent[0][1]-5-(w_b+v1_y)],
                [idt_extent[1][0]+5-idt_offset, idt_extent[1][1]+5+(w_b+v1_y)],
                layers['JOEL_FIELD']))
            c.add(gd.rectangle(
                [idt_extent[0][0]-5+idt_offset, idt_extent[0][1]-5-(w_b+v1_y)],
                [idt_extent[1][0]+5+idt_offset, idt_extent[1][1]+5+(w_b+v1_y)],
                layers['JOEL_FIELD']))
        else:
            pass  # can't break IDT into one field.

    # generate pads
    pad_extent = pads.bounding_box()

    pad_yoffset = idt_extent[1][1]+pad_extent[1][0]+pad_tapery+v1_y
    if idt_type == IDT_Type.FOCUSED:
        pad_xoffset = (g_idt/2+n_idt*lmda)*np.cos(
            theta*np.pi/360)-n_idt*lmda/2-w_b*np.sin(theta*np.pi/360)
    else:
        pad_xoffset = idt_offset

    # Single Port IDTs
    if g_idt == 0:

        if pad_rot != 0:

            for (i, j) in [(-1, 1), (1, -1)]:
                # signal connection to device
                if pad_rot == 1:
                    c.add(gd.Polygon([(i*(idt_extent[0][0]-idt_offset-M2_OVERLAP),
                                       j*(idt_extent[1][1]+v1_y)),
                                      (i*(pad_xoffset-10),
                                       j*(idt_extent[1][1]+v1_y+pad_tapery)),
                                      (i*(pad_xoffset+10),
                                       j*(idt_extent[1][1]+v1_y+pad_tapery)),
                                      (i*(idt_extent[1][0]-idt_offset+M2_OVERLAP),
                                       j*(idt_extent[1][1]+v1_y)),
                                      ], layers['M2']))
                c.add(gd.rectangle(
                    (i*(idt_extent[0][0]-idt_offset-M2_OVERLAP), j*(idt_extent[1][1])),
                    (i*(idt_extent[1][0]-idt_offset+M2_OVERLAP),
                     j*(idt_extent[1][1]+v1_y)),
                    layers['M2']))
                if idt_type == IDT_Type.OPEN:
                    pass
                else:
                    c.add(gd.rectangle(
                        (i*(idt_extent[0][0]-idt_offset), j*(idt_extent[1][1])),
                        (i*(idt_extent[1][0]-idt_offset), j*(idt_extent[1][1]+v1_y)),
                        layers['M1']))

            pad_xoffset2 = -(pad_extent[1][0]+idt_extent[0][0]+200)
            pad_yoffset2 = -pad_extent[1][1]+(idt_extent[1][1]+v1_y+pad_tapery)+70
            c.add(gd.Reference(pads,
                                   rotation=np.pi/180*0,
                                   origin=(pad_xoffset2, pad_yoffset2)))

            if pad_rot == 1:
                # Ground connection
                c.add(gd.Polygon(
                    [((pad_xoffset2+pad_extent[1][0]),
                      (idt_extent[1][1]+v1_y+pad_tapery+70)),
                     ((pad_xoffset2+pad_extent[1][0]),
                      (idt_extent[1][1]+v1_y+pad_tapery)),
                     ((pad_xoffset+10), (idt_extent[1][1]+v1_y+pad_tapery)),
                     ((pad_xoffset+10), (idt_extent[1][1]+v1_y+pad_tapery)+20),
                     ((pad_xoffset2+pad_extent[1][0])+100,
                      (idt_extent[1][1]+v1_y+pad_tapery)+20)],
                    layers['M2']
                ), )

                # Signal connection
                c.add(gd.Polygon(
                    [((pad_xoffset2+pad_extent[1][0]), pad_yoffset2-35),
                     ((pad_xoffset2+pad_extent[1][0]), pad_yoffset2+35),
                     ((pad_xoffset2+pad_extent[1][0])+100,
                      -(idt_extent[1][1]+v1_y+pad_tapery)),
                     ((pad_xoffset+10), -(idt_extent[1][1]+v1_y+pad_tapery)),
                     ((pad_xoffset+10), -(idt_extent[1][1]+v1_y+pad_tapery+20)),
                     ((pad_xoffset2+pad_extent[1][0])+100,
                      -(idt_extent[1][1]+v1_y+pad_tapery+20))],
                    layers['M2']
                ), )
            elif pad_rot == 2:
                c.add(gd.Polygon(
                    [((pad_xoffset2+pad_extent[1][0]),
                      (idt_extent[1][1]+v1_y+pad_tapery+70)),
                     ((pad_xoffset2+pad_extent[1][0]),
                      (idt_extent[1][1]+v1_y+pad_tapery)),
                     (idt_extent[0][0]-idt_offset-M2_OVERLAP,
                      idt_extent[1][1]+v1_y/2),
                     (idt_extent[0][0]-idt_offset-M2_OVERLAP,
                      idt_extent[1][1]+v1_y),
                     (idt_extent[1][0]-idt_offset+M2_OVERLAP,
                      idt_extent[1][1]+v1_y)],
                    layers['M2']
                ), )

                # Signal connection
                c.add(gd.Polygon(
                    [((pad_xoffset2+pad_extent[1][0]), pad_yoffset2-35),
                     ((pad_xoffset2+pad_extent[1][0]), pad_yoffset2+35),
                     (idt_extent[0][0]-idt_offset-M2_OVERLAP,
                      idt_extent[0][1]-v1_y/2),
                     (idt_extent[0][0]-idt_offset-M2_OVERLAP,
                      idt_extent[0][1]-v1_y),
                     (idt_extent[1][0]-idt_offset+M2_OVERLAP,
                      idt_extent[0][1]-v1_y)],
                    layers['M2']
                ), )

        else:
            c.add(gd.Reference(pads,
                                   rotation=np.pi/180*-90,
                                   origin=(-pad_xoffset, pad_yoffset)))

            pad_xoffset = 0

            for (i, j) in [(-1, 1), (1, -1)]:
                # signal connection to device
                c.add(gd.Polygon([(i*(idt_extent[0][0]-idt_offset-M2_OVERLAP),
                                   j*(idt_extent[1][1]+v1_y)),
                                  (i*(pad_xoffset-35),
                                   j*(idt_extent[1][1]+v1_y+pad_tapery)),
                                  (i*(pad_xoffset+35),
                                   j*(idt_extent[1][1]+v1_y+pad_tapery)),
                                  (i*(idt_extent[1][0]-idt_offset+M2_OVERLAP),
                                   j*(idt_extent[1][1]+v1_y)),
                                  ], layers['M2']))
                c.add(gd.rectangle(
                    (i*(idt_extent[0][0]-idt_offset-M2_OVERLAP), j*(idt_extent[1][1])),
                    (i*(idt_extent[1][0]-idt_offset+M2_OVERLAP),
                     j*(idt_extent[1][1]+v1_y)),
                    layers['M2']))
                if idt_type == IDT_Type.OPEN:
                    pass
                else:
                    c.add(gd.rectangle(
                        (i*(idt_extent[0][0]-idt_offset), j*(idt_extent[1][1])),
                        (i*(idt_extent[1][0]-idt_offset), j*(idt_extent[1][1]+v1_y)),
                        layers['M1']))

            # ground pad to pad connections
            if pad_xoffset+(pad_extent[1][1]-pad_extent[0][1])/2-70 > dev_x_extent+5:
                ground_x_offset = pad_xoffset+(pad_extent[1][1]-pad_extent[0][1])/2
            else:
                ground_x_offset = dev_x_extent+5

            g_taper = gd.Polygon([
                (-(ground_x_offset-70), (idt_extent[1][1]+pad_tapery+v1_y)),
                (-((pad_xoffset+50)), -(idt_extent[1][1]+pad_tapery+v1_y)),
                (-(pad_xoffset+70), -(idt_extent[1][1]+pad_tapery+v1_y)),
                (-(pad_xoffset+70), -(idt_extent[1][1]+pad_tapery+v1_y)-20),
                (-(ground_x_offset), (idt_extent[1][1]+pad_tapery+v1_y))
            ], layers['M2']
            )
            c.add([g_taper, gd.copy(g_taper).mirror((0, -10), (0, 10))])
            c.add(
                gd.rectangle(((pad_xoffset+70), -(idt_extent[1][1]+pad_tapery+v1_y)-20),
                             ((-(pad_xoffset+70), -(idt_extent[1][1]+pad_tapery+v1_y)))
                             , layers['M2']))

    else:
        for (i, j) in [(-1, 1), (1, -1)]:
            c.add(gd.Reference(pads,
                                   rotation=np.pi/180*i*90,
                                   origin=(i*pad_xoffset, j*pad_yoffset)))

            # signal connection to device
            c.add(gd.Polygon(
                [(i*(pad_xoffset-n_idt*lmda/2-M2_OVERLAP), j*(idt_extent[1][1]+v1_y)),
                 (i*(pad_xoffset-35), j*(idt_extent[1][1]+v1_y+pad_tapery)),
                 (i*(pad_xoffset+35), j*(idt_extent[1][1]+v1_y+pad_tapery)),
                 (i*(pad_xoffset+n_idt*lmda/2-bb_offset+M2_OVERLAP),
                  j*(idt_extent[1][1]+v1_y)),
                 ], layers['M2']))
            c.add(gd.rectangle(
                (i*(pad_xoffset-n_idt*lmda/2-M2_OVERLAP), j*(idt_extent[1][1])),
                (i*(pad_xoffset+n_idt*lmda/2-bb_offset+M2_OVERLAP),
                 j*(idt_extent[1][1]+v1_y)),
                layers['M2']))
            if idt_type == IDT_Type.OPEN:
                pass
            else:
                c.add(gd.rectangle((i*(pad_xoffset-n_idt*lmda/2), j*(idt_extent[1][1])),
                                   (i*(pad_xoffset+n_idt*lmda/2-bb_offset),
                                    j*(idt_extent[1][1]+v1_y)),
                                   layers['M1']))

            # ground pad to pad connections
            if connect_port_grounds:
                if pad_xoffset+(
                        pad_extent[1][1]-pad_extent[0][1])/2-70 > dev_x_extent+5:
                    ground_x_offset = pad_xoffset+(pad_extent[1][1]-pad_extent[0][1])/2
                else:
                    ground_x_offset = dev_x_extent+5
                c.add(gd.rectangle(
                    (i*(ground_x_offset-70), j*(idt_extent[1][1]+pad_tapery+v1_y)),
                    (i*(ground_x_offset), -j*(idt_extent[1][1]+pad_tapery+v1_y)),
                    layers['M2']))
                c.add(gd.rectangle((-i*(pad_xoffset+pad_extent[0][1]),
                                    -j*(idt_extent[1][1]+pad_tapery+v1_y)),
                                   (i*(ground_x_offset),
                                    -j*(idt_extent[1][1]+pad_tapery+v1_y+100)),
                                   layers['M2']))

            # grounded idt taper connections. For small gaps, ground connects to side
            # of v1_y busbar extension as well to prevent sharp corner.
            # if g_idt < 100:
            #     c.add(gd.Polygon([(i*(pad_xoffset-n_idt*lmda/2-M2_OVERLAP),
            #                        -j*(idt_extent[1][1]+v1_y)),
            #                       (-i*(pad_xoffset+pad_extent[0][1]+70),
            #                        -j*(idt_extent[1][1]+pad_tapery+v1_y)),
            #                       (-i*(pad_xoffset+pad_extent[0][1]),
            #                        -j*(idt_extent[1][1]+pad_tapery+v1_y)),
            #                       (i*(pad_xoffset+n_idt*lmda/2-bb_offset+M2_OVERLAP),
            #                        -j*(idt_extent[1][1])),
            #                       (i*(pad_xoffset+n_idt*lmda/2-bb_offset+M2_OVERLAP),
            #                        -j*(idt_extent[1][1]+v1_y)),
            #                       ], layers['M2']))
            # else:
            #     c.add(gd.Polygon([(i*(pad_xoffset-n_idt*lmda/2-M2_OVERLAP),
            #                        -j*(idt_extent[1][1]+v1_y)),
            #                       (-i*(pad_xoffset+pad_extent[0][1]+70),
            #                        -j*(idt_extent[1][1]+pad_tapery+v1_y)),
            #                       (-i*(pad_xoffset+pad_extent[0][1]),
            #                        -j*(idt_extent[1][1]+pad_tapery+v1_y)),
            #                       (i*(pad_xoffset+n_idt*lmda/2-bb_offset+M2_OVERLAP),
            #                        -j*(idt_extent[1][1]+v1_y)),
            #                       ], layers['M2']))
            # if g_idt < 100:

            #TODO: Fix for nidt*lmda/2 > pad pitch
            c.add(gd.Polygon([(i*(pad_xoffset+n_idt*lmda/2-bb_offset+M2_OVERLAP+2*v1_y+idt_extent[0][0]),
                               -j*(idt_extent[1][1]+v1_y)),
                              (i*(pad_xoffset+pad_extent[1][1]-70),
                               j*(idt_extent[1][1]+pad_tapery+v1_y)),
                              (i*(pad_xoffset+pad_extent[1][1]),
                               j*(idt_extent[1][1]+pad_tapery+v1_y)),
                              (i*(pad_xoffset+n_idt*lmda/2-bb_offset+M2_OVERLAP+2*v1_y+idt_extent[0][0]),
                               -j*(idt_extent[1][1]+2*v1_y)),
                              ], layers['M2']))
            c.add(gd.rectangle(
                (i*(pad_xoffset-n_idt*lmda/2-M2_OVERLAP), -j*(idt_extent[1][1])),
                (i*(pad_xoffset+n_idt*lmda/2-bb_offset+M2_OVERLAP),
                 -j*(idt_extent[1][1]+v1_y)),
                layers['M2']))
            c.add(gd.Polygon([
                (i*(pad_xoffset-n_idt*lmda/2-M2_OVERLAP+v1_y/np.arctan(pad_tapery/(35-n_idt*lmda/4))), -j*(idt_extent[1][1]+2*v1_y)),
                (i*(pad_xoffset+n_idt*lmda/2-bb_offset+M2_OVERLAP+2*v1_y+idt_extent[0][0]),
                 -j*(idt_extent[1][1]+2*v1_y)),
                (i*(pad_xoffset+n_idt*lmda/2-bb_offset+M2_OVERLAP+2*v1_y+idt_extent[0][
                    0]),
                 -j*(idt_extent[1][1]+v1_y)),
                (i*(pad_xoffset-n_idt*lmda/2-M2_OVERLAP), -j*(idt_extent[1][1]+v1_y)),
            ],
                layers['M2']))
            if idt_type == IDT_Type.OPEN:
                pass
            else:
                c.add(
                    gd.rectangle((i*(pad_xoffset-n_idt*lmda/2), -j*(idt_extent[1][1])),
                                 (i*(pad_xoffset+n_idt*lmda/2-bb_offset),
                                  -j*(idt_extent[1][1]+v1_y)),
                                 layers['M1']))
    # TODO: bloat signal pad taper and subtract from ground routing to prevent shorting for small lengths with reflectors?

    # Cell label in M2
    # c.add(gd.text(text_label,
    #               9,
    #               (-pad_xoffset-(pad_extent[1][1]-pad_extent[0][1])/2,
    #                 pad_yoffset-pad_extent[0][0]+5),
    #               layer=layers['M2']))
    for o in gd.text(text_label,
                  9,
                  (c.bounding_box()[0][0],
                   c.bounding_box()[1][1]+5),
                  layer=layers['M2']):
        c.add(o)
    return c

def idt_cell(lib, layers, w_idt, s_idt, l_idt, n_idt, w_b, s_b, label='IDT'):
    cellname = label+f'_wIDT{w_idt:.3f}_sIDT{s_idt:.3f}_nIDT{n_idt:.1f}_lIDT{l_idt:.1f}_wb{w_b:.1f}_sb{s_b:.1f}'
    try:
        c = lib.new_cell(cellname)
    except ValueError:
        return lib.cells[cellname]
    for i in range(n_idt):
        xoff = i*2*(w_idt+s_idt)-n_idt*(w_idt+s_idt)
        c.add(gd.rectangle((xoff, -l_idt/2), (xoff+w_idt, l_idt/2-s_b), layers['M1']))
        c.add(gd.rectangle((xoff+w_idt+s_idt, -l_idt/2+s_b),
                           (xoff+2*w_idt+s_idt, l_idt/2), layers['M1']))
    # idt_extents = c.bounding_box()
    # c.add(gd.rectangle((idt_extents[0][0], idt_extents[1][1]),
    #                    (idt_extents[1][0], idt_extents[1][1]+w_b),
    #                    layers['M1']))
    # c.add(gd.rectangle((idt_extents[0][0], idt_extents[0][1]),
    #                    (idt_extents[1][0], idt_extents[0][1] - w_b),
    #                    layers['M1']))
    c.add(gd.rectangle((-n_idt*(w_idt+s_idt), l_idt/2),
                       (n_idt*(w_idt+s_idt)-s_idt, l_idt/2+w_b), layers['M1']))
    c.add(gd.rectangle((-n_idt*(w_idt+s_idt), -l_idt/2),
                       (n_idt*(w_idt+s_idt)-s_idt, -l_idt/2-w_b), layers['M1']))
    return c


def idt_reflector(lib, layers, w_idt, s_idt, l_idt, n_idt, w_b):
    r = idt_cell(lib, layers, w_idt, s_idt, l_idt, n_idt, w_b, s_b=0,
                 label='focIDT_reflector')
    return r


def focused_idt_cell(lib, layers, w_idt, s_idt, theta, g_idt, n_idt, w_b, s_b,
                     label='focIDT', pad_contact=True):
    cellname = label+f'_wIDT{w_idt}_sIDT{s_idt}_nIDT{n_idt:.1f}_theta{theta:0.1f}_(g_idt{g_idt:0.1f}_wb{w_b:.1f}_sb{s_b:.1f}'
    ang = theta*np.pi/360  # half angle, radians
    try:
        c = lib.new_cell(cellname)
    except ValueError:
        return lib.cells[cellname]

    for i in range(n_idt):
        xoff = i*2*(w_idt+s_idt)
        f1 = gd.Round((0, 0), g_idt/2+xoff+w_idt, g_idt/2+xoff, -ang, ang,
                      layer=layers['M1'])
        sb1 = gd.rectangle((s_b, 0), (g_idt/2+n_idt*2*(w_idt+s_idt), -s_b),
                           layers['M1']).rotate(ang)
        c.add(gd.boolean(f1, sb1, 'not', layer=layers['M1']))

        f2 = gd.Round((0, 0), g_idt/2+xoff+2*w_idt+s_idt, g_idt/2+xoff+w_idt+s_idt,
                      -ang, ang, layer=layers['M1'])
        sb2 = gd.rectangle((s_b, 0), (g_idt/2+n_idt*2*(w_idt+s_idt), s_b),
                           layers['M1']).rotate(-ang)
        c.add(gd.boolean(f2, sb2, 'not', layer=layers['M1']))
        # c.add(gd.rectangle((xoff, -l_idt/2), (xoff+w_idt, l_idt/2-s_b), layers['M1']))
        # c.add(gd.rectangle((xoff+w_idt+s_idt, -l_idt / 2+s_b), (xoff+2*w_idt+s_idt, l_idt/2), layers['M1']))
    outer_r = g_idt/2+n_idt*2*(w_idt+s_idt)-s_idt
    # c.add(gd.rectangle((g_idt/2-outer_r*(1-np.cos(ang)), outer_r*np.sin(ang)),
    #                    (outer_r*np.cos(ang), outer_r*np.sin(ang)+w_b),
    #                    layers['M1']))
    # c.add(gd.rectangle((g_idt / 2-outer_r*(1-np.cos(ang)), -outer_r*np.sin(ang)),
    #                    (outer_r*np.cos(ang), -(outer_r*np.sin(ang)+w_b)),
    #                     layers['M1']))
    c.add(gd.rectangle((g_idt/2, 0), (outer_r, w_b), layer=layers['M1']).rotate(ang))
    c.add(gd.rectangle((g_idt/2, 0), (outer_r, -w_b), layer=layers['M1']).rotate(-ang))
    if pad_contact:
        c.add(gd.Round(center=(
        outer_r*np.cos(ang)-w_b*np.sin(ang), outer_r*np.sin(ang)+w_b*np.cos(ang)),
                       radius=outer_r-g_idt/2,
                       initial_angle=np.pi,
                       final_angle=np.pi+ang,
                       layer=layers['M1']))
        c.add(gd.Round(center=(
        outer_r*np.cos(ang)-w_b*np.sin(ang), -(outer_r*np.sin(ang)+w_b*np.cos(ang))),
                       radius=outer_r-g_idt/2,
                       initial_angle=np.pi,
                       final_angle=np.pi-ang,
                       layer=layers['M1']))
    # idt_extents = c.bounding_box()
    # c.add(gd.rectangle((idt_extents[0][0], idt_extents[1][1]),
    #                    (idt_extents[1][0], idt_extents[1][1]+w_b),
    #                    layers['M1']))
    # c.add(gd.rectangle((idt_extents[0][0], idt_extents[0][1]),
    #                    (idt_extents[1][0], idt_extents[0][1] - w_b),
    #                    layers['M1']))

    return c


def focused_idt_reflector(lib, layers, w_idt, s_idt, theta, g_idt, n_idt, w_b,
                          label='focIDT_reflector'):
    return focused_idt_cell(lib, layers, w_idt, s_idt, theta, g_idt, n_idt, w_b, s_b=0,
                            label=label, pad_contact=False)


def ewc_cell(lib, layers, lmda, process_bias, l_idt, n_idt, w_b, s_b):
    # TODO: check phase for delay between two IDTs
    cellname = f'EWC_lamda{lmda:.1f}_bias{process_bias:.1f}_nIDT{n_idt:.1f}_lIDT{l_idt:.1f}_wb{w_b:.1f}_sb{s_b:.1f}'
    try:
        c = lib.new_cell(cellname)
    except ValueError:
        return lib.cells[cellname]
    for i in range(n_idt):
        xoff = i*lmda-n_idt*lmda/2
        c.add(gd.rectangle((xoff+lmda*4/16, -l_idt/2), (xoff+lmda*6/16, l_idt/2-s_b),
                           layers['M1']))
        c.add(gd.rectangle((xoff, -l_idt/2+s_b), (xoff+lmda/8, l_idt/2), layers['M1']))
        c.add(gd.rectangle((xoff+lmda*9/16, -l_idt/2+s_b), (xoff+lmda*13/16, l_idt/2),
                           layers['M1']))
    c.add(gd.rectangle((-n_idt*lmda/2, l_idt/2), (n_idt*lmda/2-3*lmda/16, l_idt/2+w_b),
                       layers['M1']))
    c.add(
        gd.rectangle((-n_idt*lmda/2, -l_idt/2), (n_idt*lmda/2-3*lmda/16, -l_idt/2-w_b),
                     layers['M1']))
    # c.add(gd.Label('<-- fwd', (- n_idt * lmda / 2, l_idt / 2), anchor='se', layer=layers['M1']))
    return c


def dart_cell(lib, layers, lmda, process_bias, l_idt, n_idt, w_b, s_b):
    # TODO: check phase for delay between two IDTs
    cellname = f'DART_lamda{lmda:.1f}_bias{process_bias:.1f}_nIDT{n_idt:.1f}_lIDT{l_idt:.1f}_wb{w_b:.1f}_sb{s_b:.1f}'
    try:
        c = lib.new_cell(cellname)
    except ValueError:
        return lib.cells[cellname]
    for i in range(n_idt):
        xoff = i*lmda-n_idt*lmda/2
        c.add(gd.rectangle((xoff+lmda*4/16, -l_idt/2), (xoff+lmda*6/16, l_idt/2-s_b),
                           layers['M1']))
        c.add(gd.rectangle((xoff, -l_idt/2+s_b), (xoff+lmda/8, l_idt/2), layers['M1']))
        c.add(gd.rectangle((xoff+lmda*8/16, -l_idt/2+s_b), (xoff+lmda*14/16, l_idt/2),
                           layers['M1']))
    c.add(gd.rectangle((-n_idt*lmda/2, l_idt/2), (n_idt*lmda/2-lmda/8, l_idt/2+w_b),
                       layers['M1']))
    c.add(
        gd.rectangle((-n_idt*lmda/2, -l_idt/2), (n_idt*lmda/2-lmda/8, -l_idt/2-w_b),
                     layers['M1']))
    # c.add(gd.Label('<-- fwd', (- n_idt * lmda/2,l_idt/2), anchor='se', layer=layers['M1']))
    return c


def split_finger_cell(lib, layers, lmda, process_bias, l_idt, n_idt, w_b, s_b):
    # TODO: check phase for delay between two IDTs
    cellname = f'splitfinger_lamda{lmda:.1f}_bias{process_bias:.1f}_nIDT{n_idt:.1f}_lIDT{l_idt:.1f}_wb{w_b:.1f}_sb{s_b:.1f}'
    try:
        c = lib.new_cell(cellname)
    except ValueError:
        return lib.cells[cellname]
    for i in range(n_idt):
        xoff = i*lmda-n_idt*lmda/2
        c.add(gd.rectangle((xoff, -l_idt/2), (xoff+lmda/8, l_idt/2-s_b), layers['M1']))
        c.add(gd.rectangle((xoff+lmda*2/8, -l_idt/2), (xoff+lmda*3/8, l_idt/2-s_b),
                           layers['M1']))
        c.add(gd.rectangle((xoff+lmda*4/8, -l_idt/2+s_b), (xoff+lmda*5/8, l_idt/2),
                           layers['M1']))
        c.add(gd.rectangle((xoff+lmda*6/8, -l_idt/2+s_b), (xoff+lmda*7/8, l_idt/2),
                           layers['M1']))
    c.add(gd.rectangle((-n_idt*lmda/2, l_idt/2), (n_idt*lmda/2-lmda/8, l_idt/2+w_b),
                       layers['M1']))
    c.add(
        gd.rectangle((-n_idt*lmda/2, -l_idt/2), (n_idt*lmda/2-lmda/8, -l_idt/2-w_b),
                     layers['M1']))
    return c


# WIP
def alignment_marks(lib, layers, layer, l=250, w=5, w2=5, cell_prefix=''):
    '''
    Create alignment cross mark.
    5 x 250 recommended for JOEL 8100 PQRS.
    5um width min for MLA150.

    :param lib: gdspy library in which to put cell
    :param layers: layer dictionary for process
    :param layer: name of layer to place mark on
    :param l: length of marks
    :param w: width of marks at center/tips
    :param w2: width of marks in 1/8 to 3/8 region of length
    :param cell_prefix:
    :return: c: cell containing alignment mark
    '''
    #

    c = lib.new_cell(cell_prefix+f'Alignment_Mark_Layer{layer}')
    c.add(gd.rectangle((-l/2, -w/2), (-3*l/8, w/2), layers[layer]))
    c.add(gd.rectangle((-3*l/8, -w2/2), (-l/8, w2/2), layers[layer]))
    c.add(gd.rectangle((-l/8, -w/2), (l/8, w/2), layers[layer]))
    c.add(gd.rectangle((l/8, -w2/2), (3*l/8, w2/2), layers[layer]))
    c.add(gd.rectangle((3*l/8, - w/2), (l/2, w/2), layers[layer]))

    c.add(gd.rectangle((-w/2, -l/2), (w/2, -3*l/8), layers[layer]))
    c.add(gd.rectangle((-w2/2, -3*l/8), (w2/2, -l/8), layers[layer]))
    c.add(gd.rectangle((-w/2, -l/8), (w/2, l/8), layers[layer]))
    c.add(gd.rectangle((-w2/2, l/8), (w2/2, 3*l/8), layers[layer]))
    c.add(gd.rectangle((- w/2, 3*l/8), (w/2, l/2), layers[layer]))
    return c


def alignment_array(lib, layers, layer, nrow=9, ncol=9, wafer_diameter=None,
                    s_major=10000):
    c = lib.new_cell(f'Alignment_Mark_Array{layer}')
    m = alignment_marks(lib, layers, layer)

    # c.add(gd.CellArray(m, ncol, nrow, s_major,
    #                    origin=(-(s_major-1)/2*ncol, -(s_major-1)/2*nrow)))
    objs = []
    for g, x in enumerate(np.linspace(-(ncol-1)/2*s_major, (ncol-1)/2*s_major, ncol)):
        for h, y in enumerate(
                np.linspace(-(nrow-1)/2*s_major, (nrow-1)/2*s_major, nrow)):
            objs.append(gd.Reference(m, origin=(x, y)))
            objs += gd.text(f'{round(x/1000)},{round(y/1000)}',
                                size=50,
                                position=(x+175, y+175),
                                layer=layers[layer])
            if (g == ncol-1) or (h == nrow-1):
                continue
            else:
                for i in np.linspace(0, 9, 10):
                    for j in np.linspace(0, 9, 10):
                        # 1mm submarks
                        objs.append(
                            gd.rectangle((x+(i/10)*s_major-5, y+(j/10)*s_major-5),
                                         (x+(i/10)*s_major+5, y+(j/10)*s_major+5),
                                         layers[layer]))
                        objs += gd.text(f'{round(i)},{round(j)}',
                                            size=25,
                                            position=(x+(i/10)*s_major+20,
                                                      y+(j/10)*s_major+20),
                                            layer=layers[layer])
                        # # 0.5mm submarks
                        # objs.append(
                        #     gd.rectangle((x+(i/10)*s_major-3, y+(j/10+0.05)*s_major-3),
                        #                  (x+(i/10)*s_major+3, y+(j/10+0.05)*s_major+3),
                        #                  layers[layer]))
                        # objs.append(
                        #     gd.rectangle(
                        #         (x+(i/10+0.05)*s_major-3, y+(j/10)*s_major-3),
                        #         (x+(i/10+0.05)*s_major+3, y+(j/10)*s_major+3),
                        #         layers[layer]))
                        # objs.append(
                        #     gd.rectangle(
                        #         (x+(i/10+0.05)*s_major-3, y+(j/10+0.05)*s_major-3),
                        #         (x+(i/10+0.05)*s_major+3, y+(j/10+0.05)*s_major+3),
                        #         layers[layer]))
    if wafer_diameter:
        maxdim = wafer_diameter-10500  # 10mm exclusion for wafer edge
        c.add(gd.boolean(objs, gd.Round((0, 0), maxdim/2), 'and', layer=layers[layer]))
    else:
        for o in objs:
            c.add(o)
    return c


def IDT_test(lib, layers, label_layer, pitches, mratios):
    c = lib.new_cell(f'IDT_test')
    current_x = 0
    current_y0 = 0
    for p in pitches:
        for mr in mratios:
            d = idt_cell(lib, layers, mr*p, (1-mr)*p,
                         l_idt=20*p, n_idt=5, w_b=10*p, s_b=2*p)
            current_x = current_x+d.bounding_box()[1][0]-d.bounding_box()[0][
                0]+p
            current_y = current_y0+d.bounding_box()[1][1]-d.bounding_box()[0][1]
            c.add(gd.Reference(d, origin=(current_x, current_y)))
        current_x = 0
        current_y0 = current_y0+d.bounding_box()[1][1]-d.bounding_box()[0][1]
    # c.add(gd.text(f'p{p*1E3}', 21, (-10, current_y0)))  # pitch in nm
    return c


def tlm(lib, layers, pads, layer_pad, layer_line, lens, pad_offset=150):
    c = lib.new_cell(f'TLM_{layer_pad}pad_{layer_line}line_L{lens}')

    pad_extent = pads.bounding_box()
    pad_edge = pad_offset-pad_extent[1][0]
    for i, l in enumerate(lens):
        if i%2 == 0:
            rotmult = 1
        else:
            rotmult = -1
        c.add(gd.Reference(pads,
                               rotation=np.pi/180*180*(i%2),
                               origin=(rotmult*(-pad_offset), l)))

        c.add(gd.Polygon([(rotmult*(-pad_edge), l-35),
                          (rotmult*(-pad_edge), l+35),
                          (rotmult*(-pad_edge+35), l+5),
                          (rotmult*(-pad_edge+35), l-5)],
                         layers[layer_pad]))
        c.add(gd.rectangle((rotmult*(-pad_edge+25), l-5),
                           (rotmult*(pad_edge-35), l+5),
                           layers[layer_line]))

    return c


def mr_to_proc_bias(mr, lmda):
    '''converts metallization ratio to process bias'''
    return (mr-0.5)*lmda/2


lib = gd.Library('Resonator Library', unit=1E-6)
gd.current_library = lib
ds = [1, 1.5, 2, 2.5, 3, 5, 7, 10]
ys = [20, 30, 40, 50]
rs = [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]

layers = {
    'Trench': 0,
    'M1': 1,
    'M2': 2,
    'JOEL_FIELD': 50,
    'M0': 11
}

pads = gsg_pad(lib, layers, 'M1')
pads2 = gsg_pad(lib, layers, 'M2', connect_grounds=True)
# bar_resonator_matrix(lib, pads, layers, ds=ds, xs=30, ys=ys, rs=0, trench=False, yoff=10, name='matrix1')
# bar_resonator_matrix(lib, pads, layers, rs=rs, ds=[1,2], xs=30, ys=10, yoff=4, type=Bar_Type.DISC, name='matrix2')

n_idt = [10, 20, 40]
# lmbdas = 1E-3*np.array([100, 150, 200])
lmbdas = 1E-3*np.array([150, 175, 200, 250, 300, 350, 400])
# pad3 = gsg_pad(lib, layers, 'M2', connect_grounds=True)
marks = alignment_array(lib, layers, 'M0', 2, 2, wafer_diameter=None)

g_idts = [5, 10, 20, 50]

dcpad = dc_pad(lib, layers, 'M2')
# tlm(lib, layers, dcpad, 'M2', 'M1', lens=[0, 30, 80, 110])
tlm(lib, layers, dcpad, 'M2', 'M2', lens=[0, 30, 80, 110])
# IDT_test(lib, layers, 'M2', lmbdas/2, mratios=[.3, .4, .5, .75])

def stepped_IDT(pad_style, s, pix, lib: gd.Library, pads: gd.Cell, layers: dict, lmda: float,
               g_idt: float, idt_type: IDT_Type = IDT_Type.STANDARD,
               process_bias: float = 0, n_idt: int = 20, w_b: float = 5, s_b: float = 1,
               l_idt: float = None,
               reflector: bool = False, g_r: float = None, w_br: float = None,
               n_idtr: int = None, w_r: float = None,
               s_r: float = None, theta: float = None, connect_port_grounds=False,
               pad_rot: int = False, cell_prefix='') -> gd.Cell:
    
    cell_name = cell_prefix
    if s == 2:
        cell_name = cell_name+f'{row_map(s)}_open_pads'
        test_pads = 1
        test_pads_2 = 0
    if s == 3:
        cell_name = cell_name+f'{row_map(s)}_shorted_pads'
        test_pads = 1
        test_pads_2 = 1
    else:
        cell_name = cell_name+f'{row_map(s)}{map_range(pix)}'
        test_pads = 0
        test_pads_2 = 0
    c = lib.new_cell(cell_name)

    #test_pads = 0
    # if map_range(pix) > 8:
    #     test_pads = 1
    steps = 5                   # Number of steps in each finger
    Nf_in = 20                  # Default input finger pairs 
    Nf_out = 15                 # Default output finger pairs
    if s == 1 or s == 2 or s == 3:
        Nf_in = 30              # Finger pairs on the input for row A
        Nf_out = 30             # Finger pairs on the output for row A      
    pixels = pix                # Pixels in a finger width
    l = pixels * 4 * 0.5       # Lambda 
    spacing = l/4               # Spacing betweeen center of each finger
    if s in (1, 2, 3, 5, 6):      
        #width = spacing - spacing/4 # Finger width for AB EF          
        width = spacing #- spacing/4
    else:
        width = spacing - spacing/3 # Finger width for CD GH 

    bus_bar_height = 500        # Bus bar sizing
    if s == 5 or s == 4:
        constant = 20            # Distance between end of finger and opposite bus bar
    else:
        constant = 50
    Fl = 2000
    if s == 7 or s == 5:
        Fl = 550                # length of each total finger (sum of step length)
    if s == 4 or s == 6:
        Fl = 800

    io_spacing = 500 
    if s == 6 or s == 8:
        io_spacing = 120             # Distance between the input and output IDT
    if s == 5 or s == 7:
        io_spacing = 800

    tr_edge = Nf_in*spacing*4 - 3*spacing
    br_edge = Nf_in*spacing*4 + (11/5)*spacing

    bl_edge = 2*spacing + (16 * spacing) /5
    tl_edge = 0

    top_edge = bus_bar_height
    bottom_edge =  - Fl - constant - bus_bar_height

    top_BBtl = (tl_edge,top_edge)
    top_BBbr = (tr_edge, 0)
    if test_pads == 0:
        c.add(gd.rectangle(top_BBtl, top_BBbr, layer=1))

    bottom_BBtl = (bl_edge, -Fl - constant*2)
    bottom_BBbr = (br_edge, bottom_edge)
    if test_pads == 0:
        c.add(gd.rectangle(bottom_BBtl, bottom_BBbr, layer=1))

    # Add IDT
    for f in range(Nf_in): 
        # Stepped input IDT
        for i in range(steps*2):
            if i == 0:
                length = (Fl / 5) + constant
                centerx = f*4*spacing + spacing/2
                centery = 0 - length/2
                current_edge = 0 - length
            elif i < 5 :
                length = Fl/5
                centery = current_edge - length/2
                centerx = f*4*spacing + (spacing/4)*5*i + spacing/2 - (spacing * i)/2
                current_edge = current_edge - length
            elif i == 5:
                length = (Fl / 5) + constant
                centery = current_edge - constant + (length/2)
                centerx = f*4*spacing + (spacing/4)*5*(i-1) + (spacing/2)# + (spacing * 2)
                current_edge = current_edge + (Fl / 5)
                if f == 0:
                    neg_start = centerx
            elif i > 5:
                length = Fl/5
                centery = current_edge + length/2
                centerx = f*4*spacing + neg_start - (spacing/4)*5*(i-5) + (spacing * (i - 5))/2
                current_edge = current_edge + length
            Tl = (centerx - (width/2), centery + (length/2))
            Br = (centerx + (width/2), centery - (length/2))
            if test_pads == 0:
                c.add(gd.rectangle(Tl, Br, layer=1))
        
    # Standard output IDT
    # Output bus bars

    output_top_BBtl = (br_edge + io_spacing - spacing/2, top_edge)
    output_top_BBbr = (br_edge + Nf_out*4*spacing + io_spacing - 3.5*spacing, 0)

    if test_pads == 0:
        c.add(gd.rectangle(output_top_BBtl, output_top_BBbr, layer=1))

    output_bottom_BBtl = (br_edge + io_spacing + 1.5*spacing, -Fl - constant*2)
    output_bottom_BBbr = (br_edge + Nf_out*4*spacing + io_spacing - 1.5*spacing, bottom_edge)
    
    if test_pads == 0:
        c.add(gd.rectangle(output_bottom_BBtl, output_bottom_BBbr, layer=1))

    for i in range(Nf_out):
        # Centers
        cxp = br_edge + io_spacing + spacing*i*4
        cxn = br_edge + io_spacing + spacing*i*4 + spacing*2
        cyp = -Fl/2
        cyn = -Fl/2

        # Corners
        tlp = (cxp - width/2, 0)
        brp = (cxp + width/2, 2*cyp)

        tln = (cxn - width/2, - constant)
        brn = (cxn + width/2, 2*cyn - 2*constant)

        if test_pads == 0:
            c.add(gd.rectangle(tlp, brp, layer=1))
            c.add(gd.rectangle(tln, brn, layer=1))

    # Output probe pad variables
    pad_th = 80 # Thickness of each pad
    pad_off = 100 # Offset from edge of bus bar
    pad_shift = 100 # Offset from side of IDT for Pad_style == 1 
    pad_height = 80 # Height of pad
    gpad_diff = 100 # Increased height for grounding pads
    probe_space = 100 # Distance between centers of G-S-G

    # Output probe pad variables
    pad_th_out = 80
    pad_off_out = 100
    pad_shift_out = 100
    pad_height_out = 80
    gpad_diff_out = 100
    probe_space_out = 100

    if pad_style == 1:
        # First Ground Pad
        g1_tr = (bl_edge - pad_shift, bottom_edge - pad_off)
        g1_bl = (bl_edge - pad_shift - pad_th, bottom_edge - pad_off - pad_height - gpad_diff)
        c.add(gd.rectangle(g1_tr, g1_bl, layer=1))

        # Connection between G1 and bottom bus bar
        g1_tl = (bl_edge - pad_shift - pad_th, bottom_edge - pad_off)
        top_BBbl = (tl_edge,top_edge - bus_bar_height)
        bottom_BBbl = (tl_edge, bottom_edge)
        
        G1_connect = [g1_tl, g1_tr, top_BBbl , top_BBtl]
        if test_pads == 0:
            c.add(gd.Polygon(G1_connect, layer=1))

        # Signal Pad
        s_tl = (bl_edge - pad_shift - pad_th + probe_space, bottom_edge - pad_off)
        s_br = (bl_edge - pad_shift + probe_space, bottom_edge - pad_off - pad_height)
        c.add(gd.rectangle(s_tl, s_br, layer=1))

        # Signal Pad connection to bus bar
        bottom_BBbl = (bl_edge, bottom_edge)
        s_tr = (bl_edge - pad_shift + probe_space, bottom_edge - pad_off)
        s_connect_right = (bl_edge + pad_th, bottom_edge)
        s_connect = [s_tr, s_tl, bottom_BBbl, s_connect_right]
        if test_pads == 0:
            c.add(gd.Polygon(s_connect, layer=1))

        # Second Ground Pad
        g2_tr = (bl_edge - pad_shift + 2*probe_space, bottom_edge - pad_off)
        g2_bl = (bl_edge - pad_shift - pad_th + 2*probe_space, bottom_edge - pad_off - pad_height - gpad_diff)
        c.add(gd.rectangle(g2_tr, g2_bl, layer=1))

        # Ground pad connection
        g_conn = (bl_edge - pad_shift, bottom_edge - pad_off - pad_height - gpad_diff + 30)
        if test_pads == 0:
            c.add(gd.rectangle(g2_bl, g_conn, layer=1))

        # First Ground Pad (output)
        g1_tr_out = (br_edge + Nf_out*4*spacing + io_spacing - 3.5*spacing + pad_shift_out + pad_th_out - 2*probe_space_out, 
                    bus_bar_height + pad_off_out + pad_height_out + gpad_diff_out)
        g1_bl_out = (br_edge + Nf_out*4*spacing + io_spacing - 3.5*spacing + pad_shift_out - 2*probe_space_out, 
                    bus_bar_height + pad_off_out)
        c.add(gd.rectangle(g1_tr_out, g1_bl_out, layer=1))

        # Signal Pad (output)
        s_tr_out = (br_edge + Nf_out*4*spacing + io_spacing - 3.5*spacing + pad_shift_out + pad_th_out- probe_space_out, 
                    bus_bar_height + pad_off_out + pad_height_out)
        s_bl_out = (br_edge + Nf_out*4*spacing + io_spacing - 3.5*spacing + pad_shift_out - probe_space_out, 
                    bus_bar_height + pad_off_out)
        c.add(gd.rectangle(s_tr_out, s_bl_out, layer=1))

        # Signal to bus bar (output)
        s_br_out = (s_bl_out[0] + pad_th_out, s_bl_out[1])
        s_connect_left_out = (output_top_BBbr[0], output_top_BBbr[1] + bus_bar_height)
        s_connect_right_out = (output_top_BBbr[0] - pad_th_out, output_top_BBbr[1] + bus_bar_height)

        s_connect_out = [s_bl_out, s_br_out , s_connect_left_out, s_connect_right_out]
        c.add(gd.Polygon(s_connect_out, layer=1))
        
        # Second Ground Pad (output)
        g2_tr_out = (br_edge + Nf_out*4*spacing + io_spacing - 3.5*spacing + pad_shift_out + pad_th_out, 
                    bus_bar_height + pad_off_out + pad_height_out + gpad_diff_out)
        g2_bl_out = (br_edge + Nf_out*4*spacing + io_spacing - 3.5*spacing + pad_shift_out, 
                    bus_bar_height + pad_off_out)
        c.add(gd.rectangle(g2_tr_out, g2_bl_out, layer=1))

        # Connect ground pads to bus bar (output)
        g2_br_out = (g2_bl_out[0] + pad_th_out, g2_bl_out[1])
        output_bottom_BBtr = (output_bottom_BBbr[0], output_bottom_BBbr[1] + bus_bar_height - 50)

        g_to_bus_out = [g2_bl_out, g2_br_out , output_bottom_BBbr, output_bottom_BBtr]
        c.add(gd.Polygon(g_to_bus_out, layer=1))

        # Ground connection (output)
        g1_connect_out = (br_edge + Nf_out*4*spacing + io_spacing - 3.5*spacing + pad_shift_out + pad_th_out - 2*probe_space_out, 
                        bus_bar_height + pad_off_out + pad_height_out + gpad_diff_out)
        g2_connect_out = (br_edge + Nf_out*4*spacing + io_spacing - 3.5*spacing + pad_shift_out + pad_th_out - pad_th_out, 
                        bus_bar_height + pad_off_out + pad_height_out + gpad_diff_out - 30)
        c.add(gd.rectangle(g1_connect_out, g2_connect_out, layer=1))

    if pad_style == 2:

        # Signal Pad
        s_bl = (bottom_BBbr[0] - 300, 0 - Fl - constant - bus_bar_height - pad_off - pad_height)
        s_tr = (s_bl[0] - pad_th, s_bl[1] + pad_height + 10)
        c.add(gd.rectangle(s_tr, s_bl, layer=1))

        # Signal Pad connection to bus bar
        s_tl = (s_tr[0] + pad_th, s_tr[1])
        bottom_BBbl = (bottom_BBtl[0], bottom_BBbr[1])
        s_connect = [s_tl, s_tr, bottom_BBbl, bottom_BBbr]
        if test_pads == 0:
            c.add(gd.Polygon(s_connect, layer=1))

        # First Ground Pad
        g1_tr = (s_bl[0] + 100, s_bl[1] - gpad_diff)
        g1_bl = (g1_tr[0] - pad_th, g1_tr[1] + pad_height + gpad_diff)
        c.add(gd.rectangle(g1_tr, g1_bl, layer=1))

        # Second Ground Pad
        g2_tr = (g1_tr[0] - 200, g1_tr[1] + gpad_diff/2)
        g2_bl = (g1_bl[0] - 200, g1_bl[1])
        c.add(gd.rectangle(g2_tr, g2_bl, layer=1))

        # Ground pad connection
        g_conn_tl = (g2_tr[0] - (tr_edge + (spacing * steps)), g1_tr[1])
        g1_connect_point = (g1_tr[0] - pad_th, g1_tr[1] + gpad_diff/2)
        if test_pads == 0:
            c.add(gd.rectangle(g1_connect_point, g_conn_tl, layer=1))
        if test_pads == 1:
            c.add(gd.rectangle(g1_connect_point, (g2_tr[0] - pad_th, g2_tr[1] - gpad_diff/2), layer=1))

        # Connection between G1 and bottom bus bar
        g2_ext_tl = (g_conn_tl[0], g_conn_tl[1] + gpad_diff/2)
        g2_ext_bl = (g_conn_tl[0] + gpad_diff/2, g_conn_tl[1] + gpad_diff/2)
        top_BBbl = (0,0)
        top_BBtl = (0, bus_bar_height)
        G1_connect = [top_BBtl, top_BBbl, g2_ext_bl, g2_ext_tl]
        if test_pads == 0:
            c.add(gd.Polygon(G1_connect, layer=1))

        # Signal Pad (output)
        s_tr_o = (bottom_BBbr[0] + io_spacing + 300, bus_bar_height + probe_space_out + pad_height_out)
        s_bl_o = (s_tr_o[0] - pad_th_out, s_tr_o[1] - pad_height_out - 10)
        c.add(gd.rectangle(s_tr_o, s_bl_o, layer=1))

        # Signal Pad to bus bar (output)
        output_top_BBtr = (output_top_BBbr[0], output_top_BBbr[1] + bus_bar_height)
        s_br_o = (s_bl_o[0] + pad_th_out, s_bl_o[1])
        s_connect_o = [s_bl_o, s_br_o, output_top_BBtr, output_top_BBtl]
        if test_pads == 0:
            c.add(gd.Polygon(s_connect_o, layer=1))

        # First(left) Ground Pad (output)
        g1_tr_o = (s_tr_o[0] - probe_space_out, s_tr_o[1] + gpad_diff_out)
        g1_bl_o = (s_bl_o[0] - probe_space_out, s_bl_o[1] + 10)
        c.add(gd.rectangle(g1_tr_o, g1_bl_o, layer=1))

        # Second(right) Ground Pad (output)
        g2_tr_o = (s_tr_o[0] + probe_space_out, s_tr_o[1] + gpad_diff_out/2)
        g2_bl_o = (s_bl_o[0] + probe_space_out, s_bl_o[1] + 10)
        c.add(gd.rectangle(g2_tr_o, g2_bl_o, layer=1))

        # Ground Pad bridging (output)
        g_conn_tl_o = (g1_tr_o[0], g2_tr_o[1])
        if test_pads == 0:
            g_conn_br_o = (output_top_BBbr[0] + steps * 4 * spacing, g2_tr_o[1] + gpad_diff_out/2)
        if test_pads == 1:
            g_conn_br_o = (g2_tr_o[0], g2_tr_o[1] + gpad_diff_out/2)
        
        c.add(gd.rectangle(g_conn_br_o, g_conn_tl_o, layer=1))

        # Ground pad to bus bar (output)
        g_conn_tr_o = (g_conn_br_o[0], g_conn_br_o[1] - gpad_diff_out/2)
        g_conn_br_o_shifted = (g_conn_br_o[0] - gpad_diff_out/2, g_conn_br_o[1] - gpad_diff_out/2)
        output_bottom_BBtr = (output_bottom_BBbr[0], output_bottom_BBbr[1] + bus_bar_height)
        output_gnd_bus = [g_conn_br_o_shifted, g_conn_tr_o, output_bottom_BBbr, output_bottom_BBtr]
        if test_pads == 0:
            c.add(gd.Polygon(output_gnd_bus, layer=1))
        

        if test_pads_2 == 1:
            signal_short = [(s_br_o[0] - 5, s_br_o[1]), (s_bl_o[0] + 5, s_bl_o[1]), (s_tr[0] + 5, s_tr[1]), (s_tl[0] - 5, s_tl[1])]
            c.add(gd.Polygon(signal_short, layer =1))

            g_short1 = [(g1_bl_o[0] + pad_th - 15, g1_bl_o[1]), g1_bl_o, g2_bl, (g2_bl[0] + pad_th - 15, g2_bl[1])]
            c.add(gd.Polygon(g_short1, layer =1))

            g_short2 = [(g2_bl_o[0] + pad_th, g2_bl_o[1]), (g2_bl_o[0] + 15, g2_bl_o[1]), (g1_bl[0] + 15, g1_bl[1]), (g1_bl[0] + pad_th, g1_bl[1])]
            c.add(gd.Polygon(g_short2, layer =1))


def convert_file(gds_file, s , i, txt_file, invert, tool_invert):
    import klayout.lay as lay
    import klayout.db as db
    
    png_file = os.path.join(r"C:\Users\ianbc\Downloads\Saw Research\GDS_Downloads\converted_png", f"{row_map(s)}{map_range(i)}.png")
    p = 0.54

    w = 8600
    h = (w/2 - 1000)

    x1 = 0 - 500 * p
    y1 = 0 + 900 * p
    x2 = w * p - 500 * p
    y2 = -h * p + 900 * p

    lv = lay.LayoutView()

    if invert == False:
        lv.set_config("background-color", "#000000")
    else:
        lv.set_config("background-color", "#ffffff") # Pre invert

    lv.set_config("grid-visible", "false")
    lv.set_config("grid-show-ruler", "false")
    lv.set_config("text-visible", "false")
    lv.load_layout(gds_file, 0)
    lv.clear_layers()

    # establish one layer, solid fill
    lp = lay.LayerProperties()
    lp.source = "1/0"
    lp.dither_pattern = 0

    if invert == False:
        lp.fill_color = 0xffffff
        lp.frame_color = 0xffffff
    else:
        lp.fill_color = 0x000000 # Pre invert
        lp.frame_color = 0x000000 # Pre invert
    lv.insert_layer(lv.begin_layers(), lp)

    lv.max_hier()

    # Important: event processing for delayed configuration events
    # Here: triggers refresh of the image properties
    lv.timer()

    lv.save_image_with_options(png_file, w, h, 0, 0, 0, db.DBox(x1, y1, x2, y2), False)
    print("Saving png to:", os.getcwd())
    write_txt_array(png_file, w, h, s, i, txt_file, tool_invert)



def write_txt_array(file_name, x_shift, y_shift, s, i, txt_file, tool_invert):
    # Define the name of the file
    xoff = -10 # mm
    yoff = 10 # mm

    xcoordinate = xoff + ((map_range(i) - 1) * (x_shift / 1000))
    ycoordinate = yoff - ((s - 1) * (y_shift / 1000))

    # Open the file in write mode ('w' means write, and it will overwrite the file if it exists)
    with open(f'{txt_file}.txt', 'a') as file:
        file.write(f'0.45\t{tool_invert}\t{file_name}\t{xcoordinate}\t{ycoordinate}\n')
def map_range(x, in_min=15, in_max=24, out_min=1, out_max=10):
    return round(out_min + (x - in_min) * (out_max - out_min) / (in_max - in_min))

def row_map(n):
    if 1 <= n <= 9:
        return chr(ord('A') + n - 1)

pad_style = 2

testsaw = stepped_IDT(pad_style, s, i, lib, pads, layers, 5, 10)

for s in range(1, 4, 1):
    i = 48
    print(s, i)

    # Create a new library for this specific (s, i) pair
    lib = gd.Library()

    # Generate the cell using this new library
    
    # Save that specific library to an individual file
    filename = f'{row_map(s)}_{map_range(i)}.gds'
    filename = os.path.join(r"C:\Users\ianbc\Downloads\Saw Research\GDS_Downloads\large_array", f'{row_map(s)}_{map_range(i)}.gds')
    lib.write_gds(filename)
    print("Saving to:", os.path.abspath(filename))




# print(s, i)

# # Create a new library for this specific (s, i) pair
# lib = gd.Library()

# testsaw = stepped_IDT(pad_style, s, i, lib, pads, layers, 5, 10)
# # Save that specific library to an individual file
# filename = f'{row_map(s)}_{map_range(i)}.gds'
# filename = os.path.join(r"C:\Users\ianbc\Downloads\Saw Research\GDS_Downloads\conversion_test", f'{row_map(s)}_{map_range(i)}p5.gds')
# lib.write_gds(filename)
# print("Saving to:", os.path.abspath(filename))

# for s in range(1, 4, 1):
#     i = 48
#     print(s, i)

#     # Create a new library for this specific (s, i) pair
#     lib = gd.Library()

#     txt_file = 'large'
#     if s == 1 and i == 48:
#     # Empty the previous txt file
#         with open(f'{txt_file}.txt', 'w') as file:
#             file.write('')

#     # Generate the cell using this new library
#     testsaw = stepped_IDT(pad_style, s, i, lib, pads, layers, 5, 10)
#     # Save that specific library to an individual file
#     filename = f'{txt_file}_{row_map(s)}_{map_range(i)}.gds'
#     filename = os.path.join(r"C:\Users\ianbc\Downloads\Saw Research\GDS_Downloads\large_array", f'{row_map(s)}_{map_range(i)}.gds')
#     lib.write_gds(filename)
#     print("Saving to:", os.path.abspath(filename))

#     invert = False
#     tool_invert = False
#     convert_file(filename, s, i, txt_file, invert, tool_invert)
