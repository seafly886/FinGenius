const { createApp } = Vue;

createApp({
    data() {
        return {
            // 界面状态
            activeTab: 'analysis',
            stockCode: '',
            isAnalyzing: false,
            showAdvancedOptions: false,
            
            // 分析输出
            output: '',
            showOutput: false,
            reportPath: '',
            reportContent: '',
            
            // 历史记录
            analysisHistory: [],
            historyReports: [],
            
            // 事件源
            eventSource: null,
            
            // 可选参数
            options: {
                format: 'text',
                output: '',
                tts: false,
                maxSteps: 3,
                debateRounds: 2
            }
        }
    },
    methods: {
        async startAnalysis() {
            if (!this.stockCode.trim()) {
                alert('请输入股票代码');
                return;
            }

            this.isAnalyzing = true;
            this.showOutput = true;
            this.output = '';
            this.reportPath = '';
            this.reportContent = '';

            // 添加到历史记录
            const historyItem = {
                stockCode: this.stockCode,
                timestamp: new Date().toLocaleString(),
                status: 'running',
                reportPath: ''
            };
            this.analysisHistory.unshift(historyItem);

            try {
                // 构建请求参数，包含可选参数
                const requestData = {
                    stock_code: this.stockCode,
                    options: {
                        format: this.options.format,
                        output: this.options.output || null,
                        tts: this.options.tts,
                        max_steps: this.options.maxSteps,
                        debate_rounds: this.options.debateRounds
                    }
                };

                // 启动分析
                const response = await axios.post('/api/analyze', requestData);

                if (response.data.success) {
                    // 建立SSE连接获取实时输出
                    this.connectToStream(response.data.session_id);
                } else {
                    throw new Error(response.data.error || '启动分析失败');
                }
            } catch (error) {
                console.error('分析启动失败:', error);
                this.output += `错误: ${error.message}\n`;
                this.isAnalyzing = false;
                historyItem.status = 'failed';
            }
        },

        connectToStream(sessionId) {
            // 建立Server-Sent Events连接
            this.eventSource = new EventSource(`/api/stream/${sessionId}`);

            this.eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'output') {
                    this.output += data.content;
                    this.scrollToBottom();
                } else if (data.type === 'complete') {
                    this.isAnalyzing = false;
                    this.reportPath = data.report_path;
                    this.analysisHistory[0].status = 'completed';
                    this.analysisHistory[0].reportPath = data.report_path;
                    this.eventSource.close();
                    
                    // 自动加载报告内容
                    if (data.report_path) {
                        this.loadReport(data.report_path);
                        // 刷新历史报告列表
                        this.loadHistoryReports();
                    }
                } else if (data.type === 'error') {
                    this.isAnalyzing = false;
                    this.output += `\n错误: ${data.message}\n`;
                    this.analysisHistory[0].status = 'failed';
                    this.eventSource.close();
                }
            };

            this.eventSource.onerror = (error) => {
                console.error('SSE连接错误:', error);
                this.isAnalyzing = false;
                this.output += '\n连接中断，分析可能未完成\n';
                this.analysisHistory[0].status = 'failed';
                this.eventSource.close();
            };
        },

        async loadReport(reportPath) {
            try {
                const response = await axios.get(`/api/report/${encodeURIComponent(reportPath)}`);
                this.reportContent = response.data.content;
            } catch (error) {
                console.error('加载报告失败:', error);
            }
        },

        async loadHistoryReport(reportPath) {
            this.reportPath = reportPath;
            await this.loadReport(reportPath);
            // 切换到分析标签页以显示报告
            this.activeTab = 'analysis';
        },

        async downloadReport() {
            if (!this.reportPath) return;
            
            try {
                const response = await axios.get(`/api/download/${encodeURIComponent(this.reportPath)}`, {
                    responseType: 'blob'
                });
                
                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', this.reportPath.split('/').pop());
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error('下载报告失败:', error);
                alert('下载失败，请稍后重试');
            }
        },

        async viewReport() {
            if (!this.reportPath) return;
            
            // 如果是HTML报告，直接使用相对路径访问
            if (this.reportPath.includes('.html')) {
                // 提取文件名，构建正确的URL
                const fileName = this.reportPath.split('\\').pop().split('/').pop();
                window.open(`/report/html/${fileName}`, '_blank');
            } else {
                // 其他类型报告使用API视图
                window.open(`/api/view/${encodeURIComponent(this.reportPath)}`, '_blank');
            }
        },

        clearOutput() {
            this.output = '';
        },

        scrollToBottom() {
            this.$nextTick(() => {
                const container = this.$refs.outputContainer;
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            });
        },

        getStatusText(status) {
            const statusMap = {
                'running': '分析中',
                'completed': '已完成',
                'failed': '失败'
            };
            return statusMap[status] || status;
        },

        // 加载历史报告列表
        async loadHistoryReports() {
            try {
                const response = await axios.get('/api/reports');
                this.historyReports = response.data.reports;
            } catch (error) {
                console.error('加载历史报告失败:', error);
                this.historyReports = [];
            }
        },

        // 获取历史报告列表（新API）
        async getHistoryReports() {
            try {
                const response = await fetch('/api/reports/history');
                const data = await response.json();
                
                if (data.success) {
                    this.historyReports = data.reports || [];
                    this.renderHistoryReports();
                } else {
                    console.error('获取历史报告失败:', data.message);
                }
            } catch (error) {
                console.error('获取历史报告时发生错误:', error);
            }
        },

        // 删除报告（新方法）
        async deleteReportNew(reportPath, reportType) {
            if (!confirm('确定要删除这个报告吗？此操作不可撤销。')) {
                return;
            }

            try {
                const response = await fetch('/api/reports/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        report_path: reportPath,
                        report_type: reportType
                    })
                });

                const data = await response.json();
                
                if (data.success) {
                    // 删除成功，刷新历史报告列表
                    await this.getHistoryReports();
                    this.showMessage('报告删除成功', 'success');
                } else {
                    this.showMessage('删除失败: ' + data.message, 'error');
                }
            } catch (error) {
                console.error('删除报告时发生错误:', error);
                this.showMessage('删除报告时发生错误', 'error');
            }
        },

        // 获取徽章样式类
        getBadgeClass(reportType) {
            const badgeClasses = {
                'html': 'bg-primary',
                'debate': 'bg-success', 
                'research': 'bg-info',
                'battle': 'bg-warning',
                'default': 'bg-secondary'
            };
            return badgeClasses[reportType] || badgeClasses['default'];
        },

        // 显示消息
        showMessage(message, type) {
            // 简单的消息显示，可以后续改进为更好的UI
            if (type === 'success') {
                alert('✅ ' + message);
            } else {
                alert('❌ ' + message);
            }
        },

        // 渲染历史报告（占位符方法）
        renderHistoryReports() {
            // 这个方法可以用于更新UI显示
            console.log('历史报告已更新:', this.historyReports.length, '个报告');
        },

        // 打开历史报告
        openHistoryReport(reportPath) {
            this.loadHistoryReport(reportPath);
        },

        // 删除报告
        async deleteReport(reportPath, stockCode) {
            if (!confirm(`确定要删除股票 ${stockCode} 的分析报告吗？此操作不可撤销。`)) {
                return;
            }

            try {
                const response = await axios.post('/api/reports/delete', {
                    path: reportPath
                });

                if (response.data.success) {
                    alert('报告删除成功');
                    // 刷新历史报告列表
                    await this.loadHistoryReports();
                    
                    // 如果当前显示的是被删除的报告，清空显示
                    if (this.reportPath === reportPath) {
                        this.reportPath = '';
                        this.reportContent = '';
                    }
                } else {
                    throw new Error(response.data.error || '删除失败');
                }
            } catch (error) {
                console.error('删除报告失败:', error);
                alert(`删除失败: ${error.message}`);
            }
        },

        // 查看报告（在新窗口打开）
        viewHistoryReport(reportPath) {
            // 如果是HTML报告，直接使用相对路径访问
            if (reportPath.includes('.html')) {
                // 提取文件名，构建正确的URL
                const fileName = reportPath.split('\\').pop().split('/').pop();
                window.open(`/report/html/${fileName}`, '_blank');
            } else {
                // 其他类型报告使用API视图
                window.open(`/api/view/${encodeURIComponent(reportPath)}`, '_blank');
            }
        },

        // 下载历史报告
        async downloadHistoryReport(reportPath) {
            try {
                const response = await axios.get(`/api/download/${encodeURIComponent(reportPath)}`, {
                    responseType: 'blob'
                });
                
                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', reportPath.split('/').pop());
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error('下载报告失败:', error);
                alert('下载失败，请稍后重试');
            }
        },

        // 查看讨论流程
        viewDebateProcess(stockCode) {
            // 在新窗口中打开讨论流程页面
            window.open(`/debate-process.html?stock=${stockCode}`, '_blank');
        }
    },

    mounted() {
        // 页面加载时获取历史报告
        this.loadHistoryReports();
    },

    beforeUnmount() {
        // 清理SSE连接
        if (this.eventSource) {
            this.eventSource.close();
        }
    }
}).mount('#app');