/** @odoo-module */

import { registry } from "@web/core/registry"
import { KpiCard } from "./kpi_card/kpi_card"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { loadJS } from "@web/core/assets"
import { useService } from "@web/core/utils/hooks"
const { Component, onWillStart, useRef, onMounted, useState, xml } = owl
import { getColor } from "@web/views/graph/colors"
import { browser } from "@web/core/browser/browser"
import { routeToUrl } from "@web/core/browser/router_service"
var session = require('web.session');
console.log("CHECK USER", session);

// var core = require('web.core');
// console.log("CHECK USER COREEEEEEEEE", core);

var rpc = require('web.rpc');
// console.log("CHECK USER RPCCCCCCC", rpc);

export class OwlSalesDashboard extends Component {

    async fetchUsersData() {
        try {
            let users = await rpc.query({
                model: 'res.users',
                method: 'search_read',
                args: [[['id', '=', session.uid]]], // Mengambil data pengguna berdasarkan ID pengguna yang sedang login
                kwargs: {
                    fields: ['id', 'name', 'email', 'level'], // Bidang yang ingin Anda ambil
                    // limit: 1 // Kita hanya mengambil satu pengguna yang sedang login
                }
            });
            console.log("masuk 1");
            console.log("User data:", users);
            if (users.length > 0) {
                this.state.userData = users[0];
            }
        } catch (error) {
            console.error("Error fetching user data:", error);
            console.log("masuk 2");
            console.log("console erorrr", error);

        }
        console.log("masuk 3");
    }

    // top products
    async getTopProjects(){
        let domain = [['branch_id', '!=', false], ['sap_code', '!=', false]]
        if (this.state.period > 0){
            domain.push(['create_date','>', this.state.current_date])
        }

        const data = await this.orm.readGroup("project.project", domain, ['branch_id', 'task_count'], ['branch_id'], { limit: 5, orderby: "task_count desc" })

        this.state.topProjects = {
            data: {
                labels: data.map(d => d.branch_id[1]),
                  datasets: [
                  {
                    label: 'Tasks',
                    data: data.map(d => d.task_count),
                    hoverOffset: 4,
                    backgroundColor: data.map((_, index) => getColor(index)),
                  },{
                    label: 'Branches',
                    data: data.map((d, index) => index + 1), // Creatively showing branch ranking based on task count
                    hoverOffset: 4,
                    backgroundColor: data.map((_, index) => getColor(index + 5)), // Offset color index for variety
                }]
            },
            domain,
            label_field: 'branch_id',
        }
    }

    // top sales people
    // async getTopSalesPeople(){
    //     let domain = [['state', 'in', ['sale', 'done']]]
    //     if (this.state.period > 0){
    //         domain.push(['date','>', this.state.current_date])
    //     }

    //     const data = await this.orm.readGroup("sale.report", domain, ['user_id', 'price_total'], ['user_id'], { limit: 5, orderby: "price_total desc" })

    //     if (data === undefined){
    //         console.log(typeof(data))
    //         console.log("DATA", data)
    //         console.log("NO WAY HOME")
    //     } else {
    //         console.log(typeof(data))
    //         console.log("DATA", data)
    //         console.log("MUCH WAY TO GOING HOME")
    //     }

    //     this.state.topSalesPeople = {
    //         data: {
    //             labels: data.map(d => d.user_id[1]),
    //               datasets: [
    //               {
    //                 label: 'Total',
    //                 data: data.map(d => d.price_total),
    //                 hoverOffset: 4,
    //                 backgroundColor: data.map((_, index) => getColor(index)),
    //               }]
    //         },
    //         domain,
    //         label_field: 'user_id',
    //     }
    // }


    // top sales people
    // async getTopSalesPeople(){
    //     // tesdulu_masuk
    //     let domain = [['state', 'in', ['sale', 'done']]]
    //     if (this.state.period > 0){
    //         domain.push(['date','>', this.state.current_date])
    //     }

    //     // const data = await this.orm.readGroup("sale.report", domain, ['user_id', 'price_total'], ['user_id'], { limit: 5, orderby: "price_total desc" })
    //     const data = await this.orm.readGroup("sale.report", domain, ['user_id', 'price_total'], ['user_id'])
    //     // const data = 900

    //     this.state.topSalesPeople = {
    //         data: {
    //             labels: data.map(d => d.user_id[1]),
    //               datasets: [
    //               {
    //                 label: 'Total',
    //                 data: data.map(d => d.price_total),
    //                 hoverOffset: 4,
    //                 backgroundColor: data.map((_, index) => getColor(index)),
    //               }]
    //         },
    //         domain,
    //         label_field: 'user_id',
    //     }
    // }

    // digital invoice by stages
    async getDigitalInvoiceReport() {
        let domainPo = [['state', 'in', ['po', 'uploaded', 'approved']]];
        let domainGrses = [['state', 'in', ['waits', 'uploaded', 'approved']]];
        let domainBap = [['state', 'in', ['draft', 'upload', 'approve']]];
        let domainInv = [['state', 'in', ['draft', 'upload', 'approve']]];
        let domainPr = [['state', 'in', ['draft', 'upload', 'request', 'approve']]];
    
        const totalPo = await this.orm.searchCount("purchase.order", domainPo);
        const totalGrses = await this.orm.searchCount("stock.picking", domainGrses);
        const totalBap = await this.orm.searchCount("wika.berita.acara.pembayaran", domainBap);
        const totalInv = await this.orm.searchCount("account.move", domainInv);
        const totalPr = await this.orm.searchCount("wika.payment.request", domainPr);

        const data = [
            { label: 'Purchase Orders in Digital Invoicing', count: totalPo },
            { label: 'GR/SES in Digital Invoicing', count: totalGrses },
            { label: 'Berita Acara Pembayaran in Digital Invoicing', count: totalBap },
            { label: 'Invoice in Digital Invoicing', count: totalInv },
            { label: 'Pengajuan Pembayaran in Digital Invoicing', count: totalPr },
        ];
    
        this.state.digitalInvoiceReport = {
            data: {
                labels: data.map(d => d.label),
                datasets: [
                    {
                        label: 'Total',
                        data: data.map(d => d.count),
                        hoverOffset: 4,
                        backgroundColor: data.map((_, index) => getColor(index)),
                    },
                ],
            },
            domain: [domainPo, domainGrses, domainBap, domainInv, domainPr],
            label_field: 'label',
        }
    }
    

    // monthly sales
    async getMonthlySales(){
        let domain = [['state', 'in', ['draft','sent','sale', 'done']]]
        if (this.state.period > 0){
            domain.push(['date','>', this.state.current_date])
        }

        const data = await this.orm.readGroup("sale.report", domain, ['date', 'state', 'price_total'], ['date', 'state'], { orderby: "date", lazy: false })
        console.log("monthly sales", data)

        const labels = [... new Set(data.map(d => d.date))]
        const quotations = data.filter(d => d.state == 'draft' || d.state == 'sent')
        const orders = data.filter(d => ['sale','done'].includes(d.state))

        this.state.monthlySales = {
            data: {
                labels: labels,
                  datasets: [
                  {
                    label: 'Proyek',
                    data: labels.map(l=>quotations.filter(q=>l==q.date).map(j=>j.price_total).reduce((a,c)=>a+c,0)),
                    hoverOffset: 4,
                    backgroundColor: "red",
                  },{
                    label: 'Divisi Operasi',
                    data: labels.map(l=>orders.filter(q=>l==q.date).map(j=>j.price_total).reduce((a,c)=>a+c,0)),
                    hoverOffset: 4,
                    backgroundColor: "green",
                  },{
                    label: 'Divisi Fungsi',
                    data: labels.map(l=>quotations.filter(q=>l==q.date).map(j=>j.price_total).reduce((a,c)=>a+c,0)),
                    hoverOffset: 4,
                    backgroundColor: "magenta",
                  },{
                    label: 'Pusat',
                    data: labels.map(l=>orders.filter(q=>l==q.date).map(j=>j.price_total).reduce((a,c)=>a+c,0)),
                    hoverOffset: 4,
                    backgroundColor: "blue",
                  }
            ]
            },
            domain,
            label_field: 'date',
        }
    }

    // invoice monitoring
    async getInvoiceMonitoringData(){
        let domainProyek = [['approval_stage', '=', 'Proyek']]
        let domainOperasi = [['approval_stage', '=', 'Divisi Operasi']]
        let domainFungsi = [['approval_stage', '=', 'Divisi Fungsi']]
        let domainPusat = [['approval_stage', '=', 'Pusat']]

        // if (this.state.period > 0){
        //     domain.push(['date','>', this.state.current_date])
        // }

        const dataProyek = await this.orm.searchCount("account.move", domainProyek)
        const dataOperasi = await this.orm.searchCount("account.move", domainOperasi)
        const dataFungsi = await this.orm.searchCount("account.move", domainFungsi)
        const dataPusat = await this.orm.searchCount("account.move", domainPusat)
        
        const dataInvMonitoring = [
            { label: 'Invoice di Proyek', count: dataProyek },
            { label: 'Invoice di Divisi Operasi', count: dataOperasi },
            { label: 'Invoice di Divisi Fungsi', count: dataFungsi },
            { label: 'Invoice di Pusat', count: dataPusat },
        ];

        this.state.invoiceMonitoring = {
            data: {
                labels: dataInvMonitoring.map(d => d.label),
                datasets: [
                    {
                        label: 'Total',
                        data: dataInvMonitoring.map(d => d.count),
                        hoverOffset: 4,
                        backgroundColor: dataInvMonitoring.map((_, index) => getColor(index)),
                    },
                ],
            },
            domain: [domainProyek, domainOperasi, domainFungsi, domainPusat],
            label_field: 'label',
        }
    }


    // partner orders
    async getPartnerOrders(){
        let domain = [['sap_code', '!=', false]]
        if (this.state.period > 0){
            domain.push(['create_date','>', this.state.current_date])
        }

        const data = await this.orm.searchRead("res.partner", domain, ['name', 'sap_code'])
        console.log(data)

        const sapCodeCount = data.filter(d => d.sap_code).length;

        this.state.partnerOrders = {
            data: {
                labels: data.map(d => d.name),
                  datasets: [
                  {
                    label: 'Partners',
                    data: data.map(d => d.sap_code),
                    hoverOffset: 4,
                    backgroundColor: "orange",
                },
                {
                    label: 'SAP Code Count',
                    data: [sapCodeCount],
                    hoverOffset: 4,
                    backgroundColor: "blue",
                }]
            },
            domain,
            label_field: 'name',
        }
    }

    setup(){
        this.state = useState({
            uid: session.uid,
            user: session.uid,
            quotations: {
                value:10,
                percentage:6,
            },
            
            // KANBAN STATES
            po: {
                total:100,
                waits:1,
                uploaded:2,
                late:3,

                url: {
                    total:"/web/po/total",
                    wait:"/web/po/waits",
                    upload:"/web/po/uploads",
                    late:"/web/po/lates",
                },
            },
            
            grses: {
                total:100,
                waits:1,
                uploaded:2,
                late:3,
                
                url: {
                    total:"/web/grses/total",
                    wait:"/web/grses/waits",
                    upload:"/web/grses/uploads",
                    late:"/web/grses/lates",
                },
            },
            
            bap: {
                total:100,
                waits:1,
                uploaded:2,
                late:3,
                
                url: {
                    total:"/web/bap/total",
                    wait:"/web/bap/waits",
                    upload:"/web/bap/uploads",
                    late:"/web/bap/lates",
                },
            },

            inv: {
                total:100,
                waits:1,
                uploaded:2,
                late:3,

                url: {
                    total:"/web/inv/total",
                    wait:"/web/inv/waits",
                    upload:"/web/inv/uploads",
                    late:"/web/inv/lates",
                },
            },

            pr: {
                total:100,
                waits:1,
                uploaded:2,
                late:3,

                url: {
                    wait:"/web/pr/waits",
                    upload:"/web/pr/uploads",
                    late:"/web/pr/lates",
                },
            },

            pritem: {
                total:100,
                waits:1,
                uploaded:2,
                late:3,

                url: {
                    wait:"/web/pritem/waits",
                    upload:"/web/pritem/uploads",
                    late:"/web/pritem/lates",
                },
            },

            pritempus: {
                total:100,
                waits:1,
                uploaded:2,
                late:3,

                url: {
                    wait:"/web/pritempus/waits",
                    upload:"/web/pritempus/uploads",
                    late:"/web/pritempus/lates",
                },
            },

            period:90,
            // userData:[],
        })
        this.orm = useService("orm")
        this.actionService = useService("action")

        const old_chartjs = document.querySelector('script[src="/web/static/lib/Chart/Chart.js"]')
        const router = useService("router")

        if (old_chartjs){
            let { search, hash } = router.current
            search.old_chartjs = old_chartjs != null ? "0":"1"
            hash.action = 86
            browser.location.href = browser.location.origin + routeToUrl(router.current)
        }   

        // onWillUnmount(() => {
        //     this.__destroyed = true;
        // });

        onWillStart(async ()=>{
            try {
                this.getDates()
                await this.fetchUsersData()
                const promises = [
                    // PO
                    await this.getTotalPO(),
                    await this.getWaitingPO(),
                    await this.getUploadedPO(),
                    await this.getLatePO(),
                    // PO Urls
                    await this.getPoUrlWait(),
                    await this.getPoUrlUpload(),
                    await this.getPoUrlLate(),
    
                    // GRSES
                    await this.getTotalGRSES(),
                    await this.getWaitingGRSES(),
                    await this.getUploadedGRSES(),
                    await this.getLateGRSES(),
                    // GRSES Urls
                    await this.getGrsesUrlWait(),
                    await this.getGrsesUrlUpload(),
                    await this.getGrsesUrlLate(),
    
                    // BAP
                    await this.getTotalBAP(),
                    await this.getWaitingBAP(),
                    await this.getUploadedBAP(),
                    await this.getLateBAP(),
                    // BAP Urls
                    await this.getBapUrlWait(),
                    await this.getBapUrlUpload(),
                    await this.getBapUrlLate(),
    
                    // INV
                    await this.getTotalINV(),
                    await this.getWaitingINV(),
                    await this.getUploadedINV(),
                    await this.getLateINV(),
                    // INV Urls
                    await this.getInvUrlWait(),
                    await this.getInvUrlUpload(),
                    await this.getInvUrlLate(),
    
                    // PR
                    await this.getTotalPR(),
                    await this.getWaitingPR(),
                    await this.getUploadedPR(),
                    await this.getLatePR(),
    
                    // PR Urls
                    await this.getPrUrlWait(),
                    await this.getPrUrlUpload(),
                    await this.getPrUrlLate(),
    
                    // PR item
                    await this.getTotalPRitem(),
                    await this.getWaitingPRitem(),
                    await this.getUploadedPRitem(),
                    await this.getLatePRitem(),
                    
                    // PR item url
                    await this.getPrItemUrlWait(),
                    await this.getPrItemUrlUpload(),
                    await this.getPrItemUrlLate(),
    
                    // PR item pusat
                    await this.getTotalPRitempus(),
                    await this.getWaitingPRitempus(),
                    await this.getUploadedPRitempus(),
                    await this.getLatePRitempus(),
                    
                    // PR item pusat url
                    await this.getPrItemPusUrlWait(),
                    await this.getPrItemPusUrlUpload(),
                    await this.getPrItemPusUrlLate(),
    
                    // New Pie
                    await this.getDigitalInvoiceReport(),
                    
                    // Existings
                    await this.getOrders(),
                    await this.getTopProjects(),
                    // await this.getTopSalesPeople()
                    await this.getMonthlySales(),
                    await this.getInvoiceMonitoringData(),
                    await this.getPartnerOrders(),
                ];
                await Promise.all(promises);

            } catch (error) {
                console.error("Error during onWillStart:", error);
            }
        });
    }

    async onChangePeriod(){
        this.getDates()
        // await this.getQuotations()
        // PO
        // await this.fetchUsersData()
        await this.getTotalPO()
        await this.getWaitingPO()
        await this.getUploadedPO()
        await this.getLatePO()
        // PO Urls
        await this.getPoUrlWait()
        await this.getPoUrlUpload()
        await this.getPoUrlLate()

        // GRSES
        await this.getTotalGRSES()
        await this.getWaitingGRSES()
        await this.getUploadedGRSES()
        await this.getLateGRSES()
        // GRSES Urls
        await this.getGrsesUrlWait()
        await this.getGrsesUrlUpload()
        await this.getGrsesUrlLate()

        // BAP
        await this.getTotalBAP()
        await this.getWaitingBAP()
        await this.getUploadedBAP()
        await this.getLateBAP()
        // BAP Urls
        await this.getBapUrlWait()
        await this.getBapUrlUpload()
        await this.getBapUrlLate()

        // INV
        await this.getTotalINV()
        await this.getWaitingINV()
        await this.getUploadedINV()
        await this.getLateINV()
        // INV Urls
        await this.getInvUrlWait()
        await this.getInvUrlUpload()
        await this.getInvUrlLate()

        // PR
        await this.getTotalPR()
        await this.getWaitingPR()
        await this.getUploadedPR()
        await this.getLatePR()
        // PR Urls
        await this.getPrUrlWait()
        await this.getPrUrlUpload()
        await this.getPrUrlLate()
        
        // PR item
        await this.getTotalPRitem()
        await this.getWaitingPRitem()
        await this.getUploadedPRitem()
        await this.getLatePRitem()
        
        // PR item url
        await this.getPrItemUrlWait()
        await this.getPrItemUrlUpload()
        await this.getPrItemUrlLate()

        // PR item pusat
        await this.getTotalPRitempus()
        await this.getWaitingPRitempus()
        await this.getUploadedPRitempus()
        await this.getLatePRitempus()
        
        // PR item pusat url
        await this.getPrItemPusUrlWait()
        await this.getPrItemPusUrlUpload()
        await this.getPrItemPusUrlLate()

        // New Pie
        await this.getDigitalInvoiceReport()      

        // Existings
        await this.getOrders()
        await this.getTopProjects()
        // await this.getTopSalesPeople()
        await this.getMonthlySales()
        await this.getInvoiceMonitoringData()
        await this.getPartnerOrders()
    }

    getDates(){
        this.state.current_date = moment().subtract(this.state.period, 'days').format('L')
        this.state.previous_date = moment().subtract(this.state.period * 2, 'days').format('L')
    }

    // async getQuotations(){
    //     let domain = [['state', 'in', ['sent', 'draft']]]
    //     if (this.state.period > 0){
    //         domain.push(['date_order','>', this.state.current_date])
    //     }
    //     const data = await this.orm.searchCount("sale.order", domain)
    //     this.state.quotations.value = data

    //     // previous period
    //     let prev_domain = [['state', 'in', ['sent', 'draft']]]
    //     if (this.state.period > 0){
    //         prev_domain.push(['date_order','>', this.state.previous_date], ['date_order','<=', this.state.current_date])
    //     }
    //     const prev_data = await this.orm.searchCount("sale.order", prev_domain)
    //     const percentage = ((data - prev_data)/prev_data) * 100
    //     this.state.quotations.percentage = percentage.toFixed(2)
    // }


    // === PO COUNTERS ===
    async getTotalPO(){
        const menuIdPo = await this.orm.search("ir.ui.menu", [['name', '=', 'Purchase Orders']], { limit: 1 })
        const actionIdPo = await this.orm.search("ir.actions.act_window", [['context', '=', "{'default_state':'po'}"]])
        
        const dataTotal = await this.orm.searchCount("purchase.order", [])
        this.state.po.total = dataTotal
        this.state.po.url.total = `/web#action=${actionIdPo[0]}&model=purchase.order&view_type=list&cids=1&menu_id=${menuIdPo[0]}`
    }
    async getWaitingPO(){
        let domainWaiting = [
            ['status', '=', 'todo'],
            ['res_model', '=', 'purchase.order'],
            // ['state', 'in', ['today','planned']],
        ]
        const dataWaits = await this.orm.searchCount("mail.activity", domainWaiting)
        this.state.po.waits = dataWaits
    }
    async getUploadedPO(){
        let domainUploaded = [
            ['status', '=', 'to_approve'],
            ['res_model', '=', 'purchase.order'],
            // ['state', 'in', ['today','planned']],
            // ['state', '=', 'planned'],
        ]
        const dataUploaded = await this.orm.searchCount("mail.activity", domainUploaded)
        this.state.po.uploaded = dataUploaded
    }
    async getLatePO(){
        let domainLate = [
            ['res_model', '=', 'purchase.order'],
            ['is_expired', '=', true]
        ]
        const dataLate = await this.orm.searchCount("mail.activity", domainLate)
        this.state.po.late = dataLate
    }
    // ======================

    // === GRSES COUNTERS ===
    async getTotalGRSES(){
        const menuIdGr = await this.orm.search("ir.ui.menu", [['name', '=', 'GR/SES']], { limit: 1 })
        const actionIdGr = await this.orm.search("ir.actions.act_window", [['context', '=', "{'default_state':'waits'}"]])
        
        const dataTotal = await this.orm.searchCount("stock.picking", [])
        this.state.grses.total = dataTotal
        this.state.grses.url.total = `/web#action=${actionIdGr[0]}&model=stock.picking&view_type=list&cids=1&menu_id=${menuIdGr[0]}`
    }
    async getWaitingGRSES(){
        let domainWaiting = [
            ['status', '=', 'todo'],
            ['res_model', '=', 'stock.picking'],
            // ['state', 'in', ['today','planned']],
        ]
        const dataWaits = await this.orm.searchCount("mail.activity", domainWaiting)
        this.state.grses.waits = dataWaits
    }
    async getUploadedGRSES(){
        let domainUploaded = [
            ['status', '=', 'to_approve'],
            ['res_model', '=', 'stock.picking'],
            // ['state', 'in', ['today','planned']],
        ]
        const dataUploaded = await this.orm.searchCount("mail.activity", domainUploaded)
        this.state.grses.uploaded = dataUploaded
    }
    async getLateGRSES(){
        let domainLate = [
            ['res_model', '=', 'stock.picking'],
            ['is_expired', '=', true]
        ]
        const dataLate = await this.orm.searchCount("mail.activity", domainLate)
        this.state.grses.late = dataLate
    }
    // ======================
    
    // === BAP COUNTERS ===
    async getTotalBAP(){
        const menuIdBap = await this.orm.search("ir.ui.menu", [['name', '=', 'BAP']], { limit: 1 })
        const actionIdBap = await this.orm.search("ir.actions.act_window", [['res_model', '=', 'wika.berita.acara.pembayaran']])
        
        const dataTotal = await this.orm.searchCount("wika.berita.acara.pembayaran", [])
        this.state.bap.total = dataTotal
        this.state.bap.url.total = `/web#action=${actionIdBap[0]}&model=wika.berita.acara.pembayaran&view_type=list&cids=1&menu_id=${menuIdBap[0]}`
    }
    async getWaitingBAP(){
        let domainWaiting = [
            ['status', '=', 'todo'],
            ['res_model', '=', 'wika.berita.acara.pembayaran'],
            // ['state', 'in', ['today','planned']],
        ]
        const dataWaits = await this.orm.searchCount("mail.activity", domainWaiting)
        this.state.bap.waits = dataWaits
    }
    async getUploadedBAP(){
        let domainUploaded = [
            ['status', '=', 'to_approve'],
            ['res_model', '=', 'wika.berita.acara.pembayaran'],
            // ['state', 'in', ['today','planned']],
        ]
        const dataUploaded = await this.orm.searchCount("mail.activity", domainUploaded)
        this.state.bap.uploaded = dataUploaded
    }
    async getLateBAP(){
        let domainLate = [
            ['res_model', '=', 'wika.berita.acara.pembayaran'],
            ['is_expired', '=', true]
        ]
        const dataLate = await this.orm.searchCount("mail.activity", domainLate)
        this.state.bap.late = dataLate
    }
    // ======================

    // === INVOICE COUNTERS ===
    async getTotalINV(){
        const menuIdInv = await this.orm.search("ir.ui.menu", [['name', '=', 'Invoice']], { limit: 1 })
        const actionIdInv = await this.orm.search("ir.actions.act_window", [['context', '=', "{'default_move_type': 'in_invoice'}"]])
        
        const dataTotal = await this.orm.searchCount("account.move", [])
        this.state.inv.total = dataTotal
        this.state.inv.url.total = `/web#action=${actionIdInv[0]}&model=account.move&view_type=list&cids=1&menu_id=${menuIdInv[0]}`
    }
    async getWaitingINV(){
        let domainWaiting = [
            ['status', '=', 'todo'],
            ['res_model', '=', 'account.move'],
            // ['state', 'in', ['today','planned']],
        ]
        const dataWaits = await this.orm.searchCount("mail.activity", domainWaiting)
        this.state.inv.waits = dataWaits
    }
    async getUploadedINV(){
        let domainUploaded = [
            ['status', '=', 'to_approve'],
            ['res_model', '=', 'account.move'],
            // ['state', 'in', ['today','planned']],
        ]
        const dataUploaded = await this.orm.searchCount("mail.activity", domainUploaded)
        this.state.inv.uploaded = dataUploaded
    }
    async getLateINV(){
        let domainLate = [
            ['res_model', '=', 'account.move'],
            ['is_expired', '=', true]
        ]
        const dataLate = await this.orm.searchCount("mail.activity", domainLate)
        this.state.inv.late = dataLate
    }
    // ======================

    // === PR COUNTERS ===
    async getTotalPR(){
        let domainTotal = [
            ['state', 'in', ['draft','uploaded','request','approved']],
        ]
        const dataTotal = await this.orm.searchCount("wika.payment.request", [])
        this.state.pr.total = dataTotal
    }
    async getWaitingPR(){
        let domainWaiting = [
            ['status', '=', 'todo'],
            ['res_model', '=', 'wika.payment.request'],
            // ['state', 'in', ['today','planned']],
        ]
        const dataWaits = await this.orm.searchCount("mail.activity", domainWaiting)
        this.state.pr.waits = dataWaits
    }
    async getUploadedPR(){
        let domainUploaded = [
            ['status', '=', 'to_approve'],
            ['res_model', '=', 'wika.payment.request'],
            // ['state', 'in', ['today','planned']],
        ]
        const dataUploaded = await this.orm.searchCount("mail.activity", domainUploaded)
        this.state.pr.uploaded = dataUploaded
    }
    async getLatePR(){
        let domainLate = [
            ['res_model', '=', 'wika.payment.request'],
            ['is_expired', '=', true]
        ]
        const dataLate = await this.orm.searchCount("mail.activity", domainLate)
        this.state.pr.late = dataLate
    }
    // === PR item Divisi COUNTERS ===

    async getTotalPRitem() {
        const user = session.uid;
        console.log("CHECK USER LOGIN DIV", user);
        let domainTotal = [
            // ['approval_line_id.level_role', '=', 'Divisi Operasi'],
            ['next_user_id', '=', user],
        ];
        // console.log("CHECK USER LOGIN DIV", domainTotal);
        const dataTotal = await this.orm.searchCount("wika.payment.request.line", domainTotal);
        // console.log("TESTTT ADA TOTAL NYA GAK DIV", dataTotal);
        this.state.pritem.total = dataTotal;
    }
    
    
    async getWaitingPRitem() {
        let domainWaiting = [
            // ['status', '=', 'todo'],
        ];
        const dataWaits = await this.orm.searchCount("wika.payment.request.line", domainWaiting)
        this.state.pritem.waits = dataWaits
    }

    async getUploadedPRitem() {
        const user = session.uid; // Dapatkan ID pengguna yang login
        console.log("CHECK USER LOGIN DIV", user);
        let domainUploaded = [
            // ['approval_line_id.level_role', '=', 'Divisi Operasi'],
            ['next_user_id', '=', user],
        ];
        // console.log("CHECK USER LOGIN DIV", domainUploaded);
        const dataUploaded = await this.orm.searchCount("wika.payment.request.line", domainUploaded);
        // console.log("TESTTT ADA DATANYA GAK DIV", dataUploaded);
        this.state.pritem.uploaded = dataUploaded;
    }

    async getLatePRitem(){
        let domainLate = [
            ['res_model', '=', 'wika.payment.request.line'],
            ['is_expired', '=', true]
        ]
        const dataLate = await this.orm.searchCount("mail.activity", domainLate)
        this.state.pritem.late = dataLate
    }
    // ======================

    // === PR item Pusat COUNTERS ===

    async getTotalPRitempus() {
        const user = session.uid;
        let domainTotal = [
            ['approval_line_id.level_role', '=', 'Pusat'],
            ['next_user_id', '=', user],
            // ['approval_line_id.check_approval', '=', true]
            // ['next_user_id', '=', this.uid],
            // ['approval_stage', '=', 'Pusat']
        ];
        const dataTotal = await this.orm.searchCount("wika.payment.request.line", domainTotal)
        // console.log("TESTTT ADA TOTAL NYA GAK PUS", dataTotal)
        this.state.pritempus.total = dataTotal
    }
    
    async getWaitingPRitempus() {
        let domainWaiting = [
            // ['status', '=', 'todo'],
        ];
        const dataWaits = await this.orm.searchCount("wika.payment.request.line", domainWaiting)
        this.state.pritempus.waits = dataWaits
    }

    async getUploadedPRitempus() {
        const user = session.uid;
        let domainUploaded = [
            ['approval_line_id.level_role', '=', 'Pusat'],
            ['next_user_id', '=', user],
            // ['approval_line_id.check_approval', '=', true]
            // ['next_user_id', '=', this.uid],
            // ['approval_stage', '=', 'Pusat']
        ];
        const dataUploaded = await this.orm.searchCount("wika.payment.request.line", domainUploaded)
        // console.log("TESTTT ADA DATANYA GAK PUS", dataUploaded)
        this.state.pritempus.uploaded = dataUploaded
    }

    async getLatePRitempus(){
        let domainLate = [
            ['res_model', '=', 'wika.payment.request.line'],
            ['is_expired', '=', true]
        ]
        const dataLate = await this.orm.searchCount("mail.activity", domainLate)
        this.state.pritempus.late = dataLate
    }
    // ======================

    async getOrders(){
        let domain = [['state', 'in', ['sale', 'done']]]
        if (this.state.period > 0){
            domain.push(['date_order','>', this.state.current_date])
        }
        const data = await this.orm.searchCount("sale.order", domain)
        //this.state.quotations.value = data

        // previous period
        let prev_domain = [['state', 'in', ['sale', 'done']]]
        if (this.state.period > 0){
            prev_domain.push(['date_order','>', this.state.previous_date], ['date_order','<=', this.state.current_date])
        }
        const prev_data = await this.orm.searchCount("sale.order", prev_domain)
        const percentage = ((data - prev_data)/prev_data) * 100
        //this.state.quotations.percentage = percentage.toFixed(2)

        //revenues
        const current_revenue = await this.orm.readGroup("sale.order", domain, ["amount_total:sum"], [])
        const prev_revenue = await this.orm.readGroup("sale.order", prev_domain, ["amount_total:sum"], [])
        const revenue_percentage = ((current_revenue[0].amount_total - prev_revenue[0].amount_total) / prev_revenue[0].amount_total) * 100

        //average
        const current_average = await this.orm.readGroup("sale.order", domain, ["amount_total:avg"], [])
        const prev_average = await this.orm.readGroup("sale.order", prev_domain, ["amount_total:avg"], [])
        const average_percentage = ((current_average[0].amount_total - prev_average[0].amount_total) / prev_average[0].amount_total) * 100

        this.state.orders = {
            value: data,
            percentage: percentage.toFixed(2),
            revenue: `$${(current_revenue[0].amount_total/1000).toFixed(2)}K`,
            revenue_percentage: revenue_percentage.toFixed(2),
            average: `$${(current_average[0].amount_total/1000).toFixed(2)}K`,
            average_percentage: average_percentage.toFixed(2),
        }

        //this.env.services.company
    }


    // === PO URL BUILDERS ===
    async getPoUrlWait(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','Purchase Orders to Upload'],
            ['domain', '=', "[('status', '=', 'todo'), ('res_model', '=', 'purchase.order')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Purchase Orders to Upload',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'todo'), ('res_model', '=', 'purchase.order')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.po.url.wait = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.po.url.wait = url
        }
    }
    async getPoUrlUpload(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','Purchase Orders to Approve'],
            ['domain', '=', "[('status', '=', 'to_approve'), ('res_model', '=', 'purchase.order')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Purchase Orders to Approve',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'to_approve'), ('res_model', '=', 'purchase.order')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.po.url.upload = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.po.url.upload = url
        }
    }
    async getPoUrlLate(){
        // tesssss
        // debugger
        // let today = new Date().toISOString().slice(0, 10).replace(/-/g, '/')
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [['name', '=', 'Late Purchase Orders Approval'], ['domain', '=', "[('res_model', '=', 'purchase.order'), ('is_expired', '=', True)]"]]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            // debugger
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Late Purchase Orders Approval',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('res_model', '=', 'purchase.order'), ('is_expired', '=', True)]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.po.url.late = url
        } else {
            // debugger
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.po.url.late = url
        }
    }
    // === PO URL BUILDERS ===
    
    // === GRSES URL BUILDERS ===
    async getGrsesUrlWait(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','GR/SES to Upload'],
            ['domain', '=', "[('status', '=', 'todo'), ('res_model', '=', 'stock.picking')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'GR/SES to Upload',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'todo'), ('res_model', '=', 'stock.picking')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.grses.url.wait = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.grses.url.wait = url
        }
    }
    async getGrsesUrlUpload(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','GR/SES to Approve'],
            ['domain', '=', "[('status', '=', 'to_approve'), ('res_model', '=', 'stock.picking')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'GR/SES to Approve',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'to_approve'), ('res_model', '=', 'stock.picking')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.grses.url.upload = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.grses.url.upload = url
        }
    }
    async getGrsesUrlLate(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [['name', '=', 'Late GR/SES Approval'], ['domain', '=', "[('res_model', '=', 'stock.picking'), ('is_expired', '=', True)]"]]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Late GR/SES Approval',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('res_model', '=', 'stock.picking'), ('is_expired', '=', True)]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.grses.url.late = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.grses.url.late = url
        }
    }
    // === GRSES URL BUILDERS ===

    // === BAP URL BUILDERS ===
    async getBapUrlWait(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','Berita Acara Pembayaran to Upload'],
            ['domain', '=', "[('status', '=', 'todo'), ('res_model', '=', 'wika.berita.acara.pembayaran')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Berita Acara Pembayaran to Upload',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'todo'), ('res_model', '=', 'wika.berita.acara.pembayaran')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.bap.url.wait = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.bap.url.wait = url
        }
    }
    async getBapUrlUpload(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','Berita Acara Pembayaran to Approve'],
            ['domain', '=', "[('status', '=', 'to_approve'), ('res_model', '=', 'wika.berita.acara.pembayaran')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Berita Acara Pembayaran to Approve',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'to_approve'), ('res_model', '=', 'wika.berita.acara.pembayaran')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.bap.url.upload = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.bap.url.upload = url
        }
    }
    async getBapUrlLate(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [['name', '=', 'Late Berita Acara Pembayaran Approval'], ['domain', '=', "[('res_model', '=', 'wika.berita.acara.pembayaran'), ('is_expired', '=', True)]"]]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Late Berita Acara Pembayaran Approval',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('res_model', '=', 'wika.berita.acara.pembayaran'), ('is_expired', '=', True)]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.bap.url.late = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.bap.url.late = url
        }
    }
    // === BAP URL BUILDERS ===

    // === INV URL BUILDERS ===
    async getInvUrlWait(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name', '=', 'Invoice to Upload'],
            ['domain', '=', "[('status', '=', 'todo'), ('res_model', '=', 'account.move')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Invoice to Upload',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'todo'), ('res_model', '=', 'account.move')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.inv.url.wait = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.inv.url.wait = url
        }
    }
    async getInvUrlUpload(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','Invoice to Approve'],
            ['domain', '=', "[('status', '=', 'to_approve'), ('res_model', '=', 'account.move')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Invoice to Approve',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'to_approve'), ('res_model', '=', 'account.move')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.inv.url.upload = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.inv.url.upload = url
        }
    }
    async getInvUrlLate(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [['name', '=', 'Late Invoice Approval'], ['domain', '=', "[('res_model', '=', 'account.move'), ('is_expired', '=', True)]"]]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Late Invoice Approval',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('res_model', '=', 'account.move'), ('is_expired', '=', True)]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.inv.url.late = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.inv.url.late = url
        }
    }
    // === INV URL BUILDERS ===

    // === PR URL BUILDERS ===
    async getPrUrlWait(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','Pengajuan Pembayaran to Upload'],
            ['domain', '=', "[('status', '=', 'todo'), ('res_model', '=', 'wika.payment.request')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Pengajuan Pembayaran to Upload',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'todo'), ('res_model', '=', 'wika.payment.request')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.pr.url.wait = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.pr.url.wait = url
        }
    }
    async getPrUrlUpload(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','Pengajuan Pembayaran to Approve'],
            ['domain', '=', "[('status', '=', 'to_approve'), ('res_model', '=', 'wika.payment.request')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Pengajuan Pembayaran to Approve',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'to_approve'), ('res_model', '=', 'wika.payment.request')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.pr.url.upload = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.pr.url.upload = url
        }
    }
    async getPrUrlLate(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [['name', '=', 'Late Pengajuan Pembayaran Approval'], ['domain', '=', "[('res_model', '=', 'wika.payment.request'), ('is_expired', '=', True)]"]]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Late Pengajuan Pembayaran Approval',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('res_model', '=', 'wika.payment.request'), ('is_expired', '=', True)]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.pr.url.late = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.pr.url.late = url
        }
    }
    // === PR URL BUILDERS ===

    // === PR ITEM DIVISI URL BUILDERS
    async getPrItemUrlWait(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','Payment Request Item to Upload'],
            ['domain', '=', "[('status', '=', 'todo'), ('res_model', '=', 'wika.payment.request.line')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Payment Request Item to Upload',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'todo'), ('res_model', '=', 'wika.payment.request.line')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.pritem.url.wait = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.pritem.url.wait = url
        }
    }
    
    async getPrItemUrlUpload() {
        const model = 'wika.payment.request.line';
        const menuId = await this.orm.search("ir.ui.menu", [['name', '=', 'Dashboard']]);
        
        const actionId = 745;
        
        let domain = [
            ['approval_line_id.level_role', '=', 'Divisi Operasi'],
            // ['next_user_id', '=', user],
        ];
        
        const url = `/web#action=${actionId}&model=${model}&view_type=list&cids=1&menu_id=${menuId}&domain=${JSON.stringify(domain)}`;
        this.state.pritem.url.upload = url;
    }

    async getPrItemUrlLate(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [['name', '=', 'Late Pengajuan Pembayaran Approval'], ['domain', '=', "[('res_model', '=', 'wika.payment.request.line'), ('is_expired', '=', True)]"]]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Late Pengajuan Pembayaran Approval',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('res_model', '=', 'wika.payment.request.line'), ('is_expired', '=', True)]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.pritem.url.late = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.pritem.url.late = url
        }
        console.log("LATE PR URL --->", this.state.pr.url.late)
    }
    // === PR ITEM DIVISI URL BUILDERS

    // === PR ITEM PUSAT URL BUILDERS
    async getPrItemPusUrlWait(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [
            ['name','=','Payment Request Item to Upload'],
            ['domain', '=', "[('status', '=', 'todo'), ('res_model', '=', 'wika.payment.request.line')]"]
        ]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Payment Request Item to Upload',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('status', '=', 'todo'), ('res_model', '=', 'wika.payment.request.line')]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.pritempus.url.wait = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.pritempus.url.wait = url
        }
    }

    async getPrItemPusUrlUpload() {
        const model = 'wika.payment.request.line';
        const menuId = await this.orm.search("ir.ui.menu", [['name', '=', 'Dashboard']]);
        
        const actionId = 745;
        const user = session.uid;
        
        let domain = [
            ['approval_line_id.level_role', '=', 'Pusat'],
            ['next_user_id', '=', user],
        ];
        // console.log("CHECK LEVEL ROLE DAN UUID")
        
        const url = `/web#action=${actionId}&model=${model}&view_type=list&cids=1&menu_id=${menuId}&domain=${JSON.stringify(domain)}`;
        this.state.pritempus.url.upload = url;
    }
    
    async getPrItemPusUrlLate(){
        let domainView = [['name', '=', 'mail.activity.todo.view.tree'], ['model', '=', 'mail.activity']]
        let domainMenu = [['name', '=', 'Dashboard'], ['web_icon', 'ilike', 'wika_dashboard']]
        let domainAction = [['name', '=', 'Late Pengajuan Pembayaran Approval'], ['domain', '=', "[('res_model', '=', 'wika.payment.request.line'), ('is_expired', '=', True)]"]]
        const viewId = await this.orm.search("ir.ui.view", domainView)
        const existingAction = await this.orm.search("ir.actions.act_window", domainAction)
        const menuId = await this.orm.search("ir.ui.menu", domainMenu)

        if (existingAction[0] === 0 || existingAction.length === 0) {
            const actionId = await this.orm.create('ir.actions.act_window', [{
                name: 'Late Pengajuan Pembayaran Approval',
                res_model: 'mail.activity',
                view_mode: 'tree',
                view_id: viewId[0],
                domain: "[('res_model', '=', 'wika.payment.request.line'), ('is_expired', '=', True)]"
            }])
            let url = `/web#model=mail.activity&view_type=list&action=${actionId}&menu_id=${menuId}`
            this.state.pritempus.url.late = url
        } else {
            let url = `/web#model=mail.activity&view_type=list&action=${existingAction}&menu_id=${menuId}`
            this.state.pritempus.url.late = url
        }
        console.log("LATE PR URL --->", this.state.pr.url.late)
    }
    // === PR ITEM PUSAT URL BUILDERS
    async viewQuotations(){
        let domain = [['state', 'in', ['sent', 'draft']]]
        if (this.state.period > 0){
            domain.push(['date_order','>', this.state.current_date])
        }

        let list_view = await this.orm.searchRead("ir.model.data", [['name', '=', 'view_quotation_tree_with_onboarding']], ['res_id'])

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Quotations",
            res_model: "sale.order",
            domain,
            views: [
                [list_view.length > 0 ? list_view[0].res_id : false, "list"],
                [false, "form"],
            ]
        })
    }

    async viewTotalPO(){
        let domainTotalPO = [
            ['state', 'in', ['po','uploaded','approved']],
        ]
        
        let list_view = await this.orm.searchRead("ir.model.data", [['name', '=', 'purchase_order_tree_wika']], ['res_id'])
        let form_view = await this.orm.searchRead("ir.model.data", [['name', '=', 'purchase_order_form_wika']], ['res_id'])

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "All Purchase Orders in Digital Invoicing",
            res_model: "purchase.order",
            domainTotalPO,
            views: [
                [list_view.length > 0 ? list_view[0].res_id : false, "list"],
                [form_view.length > 0 ? form_view[0].res_id : false, "form"],
            ]
        })
    }

    viewOrders(){
        let domain = [['state', 'in', ['sale', 'done']]]
        if (this.state.period > 0){
            domain.push(['date_order','>', this.state.current_date])
        }

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Quotations",
            res_model: "sale.order",
            domain,
            context: {group_by: ['date_order']},
            views: [
                [false, "list"],
                [false, "form"],
            ]
        })
    }

    viewRevenues(){
        let domain = [['state', 'in', ['sale', 'done']]]
        if (this.state.period > 0){
            domain.push(['date_order','>', this.state.current_date])
        }

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Quotations",
            res_model: "sale.order",
            domain,
            context: {group_by: ['date_order']},
            views: [
                [false, "pivot"],
                [false, "form"],
            ]
        })
    }
}

OwlSalesDashboard.template = "owl.OwlSalesDashboard"
OwlSalesDashboard.components = { KpiCard, ChartRenderer }

registry.category("actions").add("owl.sales_dashboard", OwlSalesDashboard)
